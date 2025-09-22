# apps/triage/serializers.py
"""
Serializers para API REST do sistema de triagem
Implementa validações médicas e segurança HIPAA
"""

from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from apps.triage.models import Patient, TriageSession, TriageAuditLog
from apps.facilities.models import Facility
from apps.triage.manchester import ManchesterTriageSystem
import logging

logger = logging.getLogger(__name__)


class PatientSerializer(serializers.ModelSerializer):
    """
    Serializer para dados do paciente
    Campos sensíveis são mascarados para usuários não autorizados
    """
    age = serializers.ReadOnlyField()
    age_months = serializers.ReadOnlyField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'birth_date',
            'gender', 'age', 'age_months', 'blood_type', 'allergies',
            'chronic_conditions', 'current_medications', 'preferred_language',
            'needs_accessibility', 'accessibility_notes'
        ]
        read_only_fields = ['id', 'age', 'age_months']
    
    def get_full_name(self, obj):
        """Retorna nome completo ou iniciais baseado em permissão"""
        request = self.context.get('request')
        if request and request.user.has_permission('view_full_patient_data'):
            return f"{obj.first_name} {obj.last_name}"
        # Retorna apenas iniciais para privacidade
        return f"{obj.first_name[0]}. {obj.last_name[0]}."
    
    def to_representation(self, instance):
        """Remove campos sensíveis se usuário não tem permissão"""
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        if not request or not request.user.has_permission('view_phi'):
            # Remove dados sensíveis
            sensitive_fields = ['birth_date', 'allergies', 'chronic_conditions', 
                              'current_medications', 'blood_type']
            for field in sensitive_fields:
                data.pop(field, None)
        
        return data


class VitalSignsSerializer(serializers.Serializer):
    """Validação de sinais vitais com ranges médicos"""
    blood_pressure_systolic = serializers.IntegerField(
        min_value=60, max_value=250, required=False,
        help_text="Pressão sistólica em mmHg"
    )
    blood_pressure_diastolic = serializers.IntegerField(
        min_value=30, max_value=150, required=False,
        help_text="Pressão diastólica em mmHg"
    )
    heart_rate = serializers.IntegerField(
        min_value=30, max_value=250, required=False,
        help_text="Frequência cardíaca em bpm"
    )
    respiratory_rate = serializers.IntegerField(
        min_value=8, max_value=60, required=False,
        help_text="Frequência respiratória em rpm"
    )
    temperature = serializers.FloatField(
        min_value=34.0, max_value=42.0, required=False,
        help_text="Temperatura em Celsius"
    )
    spo2 = serializers.IntegerField(
        min_value=50, max_value=100, required=False,
        help_text="Saturação de O2 em %"
    )
    glucose = serializers.IntegerField(
        min_value=20, max_value=800, required=False,
        help_text="Glicemia em mg/dL"
    )
    gcs = serializers.IntegerField(
        min_value=3, max_value=15, required=False,
        help_text="Glasgow Coma Scale"
    )
    pain_scale = serializers.IntegerField(
        min_value=0, max_value=10, required=False,
        help_text="Escala de dor 0-10"
    )
    
    def validate(self, data):
        """Validações cruzadas de sinais vitais"""
        if 'blood_pressure_systolic' in data and 'blood_pressure_diastolic' in data:
            if data['blood_pressure_systolic'] <= data['blood_pressure_diastolic']:
                raise serializers.ValidationError(
                    "Pressão sistólica deve ser maior que diastólica"
                )
        
        # Alerta para valores críticos
        critical_values = []
        if data.get('spo2', 100) < 90:
            critical_values.append('SpO2 crítico')
        if data.get('blood_pressure_systolic', 120) < 90:
            critical_values.append('Hipotensão')
        if data.get('heart_rate', 80) > 150 or data.get('heart_rate', 80) < 50:
            critical_values.append('FC anormal')
        
        if critical_values:
            logger.warning(f"Valores críticos detectados: {', '.join(critical_values)}")
        
        return data


class TriageSessionSerializer(serializers.ModelSerializer):
    """
    Serializer principal para sessões de triagem
    Implementa o protocolo Manchester completo
    """
    patient = PatientSerializer(read_only=True)
    patient_id = serializers.UUIDField(write_only=True, required=False)
    patient_cpf = serializers.CharField(write_only=True, required=False)
    vital_signs = VitalSignsSerializer(required=False)
    priority_display = serializers.CharField(source='get_priority_color_display', read_only=True)
    recommendations = serializers.SerializerMethodField()
    estimated_wait = serializers.SerializerMethodField()
    
    class Meta:
        model = TriageSession
        fields = [
            'id', 'session_uuid', 'patient', 'patient_id', 'patient_cpf',
            'facility', 'arrival_time', 'chief_complaint', 'complaint_description',
            'symptom_duration_hours', 'pain_scale', 'manchester_flowchart',
            'discriminators_answered', 'vital_signs', 'priority_color',
            'priority_level', 'priority_reason', 'priority_display',
            'status', 'queue_position', 'estimated_wait_minutes',
            'recommendations', 'estimated_wait', 'triage_notes',
            'clinical_override', 'override_reason'
        ]
        read_only_fields = [
            'id', 'session_uuid', 'priority_color', 'priority_level',
            'priority_reason', 'queue_position', 'estimated_wait_minutes'
        ]
    
    def get_recommendations(self, obj):
        """Retorna recomendações baseadas na prioridade"""
        return obj.get_recommendations()
    
    def get_estimated_wait(self, obj):
        """Calcula tempo estimado de espera"""
        if obj.status == 'WAITING':
            return obj.update_wait_time_estimate()
        return 0

    def get_recommended_facilities(self, obj):
        """Retorna unidades recomendadas baseado na triagem"""
        if obj.status != 'WAITING':
            return []

        from apps.triage.routing import TriageRouter
        router = TriageRouter()

        # Pega coordenadas do request se disponível
        request = self.context.get('request')
        lat = lng = None
        if request:
            lat = request.query_params.get('lat')
            lng = request.query_params.get('lng')
            if lat and lng:
                lat, lng = float(lat), float(lng)

        return router.route_patient(obj, lat, lng)

    def validate(self, data):
        """Validação completa dos dados de triagem"""
        # Identifica ou cria paciente
        if not data.get('patient_id') and not data.get('patient_cpf'):
            raise serializers.ValidationError(
                "É necessário informar patient_id ou patient_cpf"
            )
        
        # Valida fluxograma Manchester
        mts = ManchesterTriageSystem()
        flowchart = data.get('manchester_flowchart')
        if flowchart and flowchart not in mts.flowcharts:
            raise serializers.ValidationError(
                f"Fluxograma inválido: {flowchart}"
            )
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Cria nova sessão de triagem com cálculo Manchester
        Usa transação para garantir consistência
        """
        # Extrai dados nested
        vital_signs = validated_data.pop('vital_signs', {})
        patient_cpf = validated_data.pop('patient_cpf', None)
        patient_id = validated_data.pop('patient_id', None)
        
        # Identifica paciente
        if patient_id:
            patient = Patient.objects.get(id=patient_id)
        elif patient_cpf:
            patient = Patient.objects.get(cpf=patient_cpf)
        else:
            raise serializers.ValidationError("Paciente não identificado")
        
        # Calcula prioridade Manchester
        mts = ManchesterTriageSystem()
        priority, reason, recommendations = mts.calculate_priority(
            complaint=validated_data['manchester_flowchart'],
            discriminator_answers=validated_data.get('discriminators_answered', {}),
            vital_signs=vital_signs,
            patient_age_months=patient.age_months
        )
        
        # Cria sessão
        session = TriageSession.objects.create(
            patient=patient,
            vital_signs=vital_signs,
            priority_color=priority.name,
            priority_level=priority.value[0],
            priority_reason=reason,
            triage_start_time=timezone.now(),
            triage_nurse=self.context['request'].user,
            **validated_data
        )
        
        # Calcula posição na fila
        session.queue_position = session.calculate_queue_position()
        session.estimated_wait_minutes = session.update_wait_time_estimate()
        session.save()
        
        # Log de auditoria
        TriageAuditLog.objects.create(
            session=session,
            action='TRIAGE_CREATED',
            performed_by=self.context['request'].user,
            details={
                'priority': priority.name,
                'reason': reason,
                'vital_signs': vital_signs
            }
        )
        
        logger.info(f"Nova triagem criada: {session.id} - Prioridade {priority.name}")
        
        return session
    
    def update(self, instance, validated_data):
        """Atualização de triagem com log de auditoria"""
        # Campos que não podem ser alterados
        immutable_fields = ['patient', 'facility', 'arrival_time', 'session_uuid']
        for field in immutable_fields:
            validated_data.pop(field, None)
        
        # Salva estado anterior para auditoria
        old_priority = instance.priority_color
        old_status = instance.status
        
        # Atualiza campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Se mudou prioridade, recalcula fila
        if old_priority != instance.priority_color:
            instance.queue_position = instance.calculate_queue_position()
            instance.estimated_wait_minutes = instance.update_wait_time_estimate()
        
        instance.save()
        
        # Log de auditoria
        TriageAuditLog.objects.create(
            session=instance,
            action='TRIAGE_UPDATED',
            performed_by=self.context['request'].user,
            details={
                'old_priority': old_priority,
                'new_priority': instance.priority_color,
                'old_status': old_status,
                'new_status': instance.status,
                'changes': validated_data
            }
        )
        
        return instance


class FacilitySerializer(serializers.ModelSerializer):
    """Serializer para unidades de saúde"""
    current_queue = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()
    
    class Meta:
        model = Facility
        fields = [
            'id', 'name', 'facility_type', 'address', 'city', 'state',
            'latitude', 'longitude', 'phone_primary', 'phone_emergency',
            'is_24h', 'opening_time', 'closing_time', 'manchester_enabled',
            'is_accepting_emergencies', 'is_accepting_walkins',
            'current_occupancy_percent', 'current_queue', 'distance_km',
            'is_open', 'resources', 'specialties'
        ]
    
    def get_current_queue(self, obj):
        """Retorna estado atual das filas"""
        return obj.get_current_queue_status()
    
    def get_distance_km(self, obj):
        """Calcula distância do usuário"""
        request = self.context.get('request')
        if request and 'lat' in request.GET and 'lng' in request.GET:
            try:
                lat = float(request.GET['lat'])
                lng = float(request.GET['lng'])
                return round(obj.calculate_distance_from(lat, lng), 1)
            except (ValueError, TypeError):
                pass
        return None
    
    def get_is_open(self, obj):
        """Verifica se está aberto agora"""
        return obj.is_open_now()


# apps/triage/views.py
"""
ViewSets para API REST do sistema de triagem
Implementa endpoints com permissões médicas apropriadas
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from django.utils import timezone
from apps.triage.models import Patient, TriageSession
from apps.facilities.models import Facility
from apps.triage.serializers import (
    PatientSerializer, TriageSessionSerializer, FacilitySerializer
)
from apps.triage.permissions import MedicalPermission
import logging

logger = logging.getLogger(__name__)


class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de pacientes
    Requer autenticação e permissões médicas
    """
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated, MedicalPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'cpf']
    filterset_fields = ['gender', 'blood_type']
    
    def get_queryset(self):
        """Filtra pacientes baseado em permissões"""
        queryset = super().get_queryset()
        
        # Se não é admin, mostra apenas pacientes da mesma facility
        if not self.request.user.role == 'ADMIN':
            queryset = queryset.filter(
                triage_sessions__facility=self.request.user.facility
            ).distinct()
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def medical_history(self, request, pk=None):
        """Retorna histórico médico do paciente"""
        patient = self.get_object()
        
        # Verifica permissão específica
        if not request.user.has_permission('view_medical_history'):
            return Response(
                {'detail': 'Sem permissão para visualizar histórico médico'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Busca últimas 10 sessões de triagem
        sessions = TriageSession.objects.filter(
            patient=patient
        ).order_by('-arrival_time')[:10]
        
        serializer = TriageSessionSerializer(sessions, many=True, context={'request': request})
        
        return Response({
            'patient': PatientSerializer(patient).data,
            'history': serializer.data
        })


class TriageSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal para sessões de triagem
    Gerencia todo o fluxo de atendimento
    """
    queryset = TriageSession.objects.all()
    serializer_class = TriageSessionSerializer
    permission_classes = [IsAuthenticated, MedicalPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'priority_color', 'facility']
    ordering_fields = ['priority_level', 'arrival_time']
    ordering = ['priority_level', 'arrival_time']
    
    def get_queryset(self):
        """Filtra sessões baseado em facility e status"""
        queryset = super().get_queryset()
        
        # Filtra por facility do usuário (exceto admin)
        if self.request.user.role != 'ADMIN':
            queryset = queryset.filter(facility=self.request.user.facility)
        
        # Filtra por status ativo por padrão
        if self.action == 'list':
            active_only = self.request.query_params.get('active', 'true')
            if active_only.lower() == 'true':
                queryset = queryset.filter(
                    status__in=['ARRIVAL', 'TRIAGE', 'WAITING', 'IN_CARE', 'OBSERVATION']
                )
        
        return queryset.select_related('patient', 'facility', 'triage_nurse')
    
    @action(detail=False, methods=['get'])
    def queue(self, request):
        """
        Retorna fila atual organizada por prioridade Manchester
        Endpoint principal para dashboard
        """
        facility_id = request.query_params.get('facility', request.user.facility_id)
        
        sessions = TriageSession.objects.filter(
            facility_id=facility_id,
            status='WAITING'
        ).order_by('priority_level', 'arrival_time')
        
        # Organiza por cor
        queue_by_color = {
            'RED': [],
            'ORANGE': [],
            'YELLOW': [],
            'GREEN': [],
            'BLUE': [],
        }
        
        for session in sessions:
            queue_by_color[session.priority_color].append(
                TriageSessionSerializer(session, context={'request': request}).data
            )
        
        # Estatísticas
        stats = {
            'total_waiting': sessions.count(),
            'critical_count': sessions.filter(
                priority_color__in=['RED', 'ORANGE']
            ).count(),
            'average_wait_time': sessions.aggregate(
                avg=Avg('estimated_wait_minutes')
            )['avg'] or 0,
            'last_update': timezone.now().isoformat()
        }
        
        return Response({
            'queue': queue_by_color,
            'statistics': stats
        })
    
    @action(detail=True, methods=['post'])
    def call_patient(self, request, pk=None):
        """Chama paciente para atendimento"""
        session = self.get_object()
        room = request.data.get('room', 'Consultório 1')
        
        # Verifica se pode chamar
        if session.status != 'WAITING':
            return Response(
                {'detail': 'Paciente não está aguardando'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Atualiza status
        session.status = 'IN_CARE'
        session.called_time = timezone.now()
        session.attendance_start_time = timezone.now()
        session.save()
        
        # Log
        logger.info(f"Paciente chamado: {session.id} para {room}")
        
        # Notificação via WebSocket seria disparada aqui
        
        return Response({
            'message': 'Paciente chamado com sucesso',
            'room': room,
            'patient': session.patient.first_name
        })
    
    @action(detail=True, methods=['post'])
    def discharge(self, request, pk=None):
        """Alta do paciente"""
        session = self.get_object()
        
        discharge_type = request.data.get('type', 'DISCHARGED')
        notes = request.data.get('notes', '')
        
        session.status = discharge_type
        session.discharge_time = timezone.now()
        session.medical_notes = notes
        
        # Calcula tempo total
        session.total_wait_time_minutes = (
            session.discharge_time - session.arrival_time
        ).seconds // 60
        
        session.save()
        
        return Response({
            'message': 'Alta registrada',
            'total_time_minutes': session.total_wait_time_minutes
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Estatísticas do dia para dashboard gerencial
        """
        facility_id = request.query_params.get('facility', request.user.facility_id)
        today = timezone.now().date()
        
        sessions = TriageSession.objects.filter(
            facility_id=facility_id,
            arrival_time__date=today
        )
        
        stats = sessions.aggregate(
            total=Count('id'),
            red_count=Count('id', filter=Q(priority_color='RED')),
            orange_count=Count('id', filter=Q(priority_color='ORANGE')),
            yellow_count=Count('id', filter=Q(priority_color='YELLOW')),
            green_count=Count('id', filter=Q(priority_color='GREEN')),
            blue_count=Count('id', filter=Q(priority_color='BLUE')),
            avg_wait=Avg('total_wait_time_minutes'),
            discharged=Count('id', filter=Q(status='DISCHARGED')),
            transferred=Count('id', filter=Q(status='TRANSFERRED')),
            left=Count('id', filter=Q(status='LEFT'))
        )
        
        # Taxa LWBS (Left Without Being Seen)
        if stats['total'] > 0:
            stats['lwbs_rate'] = (stats['left'] / stats['total']) * 100
        else:
            stats['lwbs_rate'] = 0
        
        # Tempo médio por prioridade
        priority_times = {}
        for color in ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']:
            avg = sessions.filter(
                priority_color=color,
                total_wait_time_minutes__isnull=False
            ).aggregate(avg=Avg('total_wait_time_minutes'))['avg']
            priority_times[color] = avg or 0
        
        stats['average_by_priority'] = priority_times
        
        return Response(stats)


class FacilityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para unidades de saúde
    Apenas leitura para usuários normais
    """
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'city']
    filterset_fields = ['facility_type', 'is_24h', 'is_accepting_emergencies']
    
    def get_queryset(self):
        """Otimiza queryset e permite filtro por distância"""
        queryset = super().get_queryset()
        
        # Filtra por distância se coordenadas fornecidas
        lat = self.request.query_params.get('lat')
        lng = self.request.query_params.get('lng')
        max_distance = self.request.query_params.get('max_distance', 50)
        
        if lat and lng:
            try:
                lat = float(lat)
                lng = float(lng)
                max_distance = float(max_distance)
                
                # Filtra facilities dentro do raio
                nearby_facilities = []
                for facility in queryset:
                    distance = facility.calculate_distance_from(lat, lng)
                    if distance <= max_distance:
                        nearby_facilities.append(facility.id)
                
                queryset = queryset.filter(id__in=nearby_facilities)
            except (ValueError, TypeError):
                pass
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def real_time_status(self, request, pk=None):
        """Status em tempo real da unidade"""
        facility = self.get_object()
        
        return Response({
            'facility': FacilitySerializer(facility, context={'request': request}).data,
            'queue_status': facility.get_current_queue_status(),
            'is_open': facility.is_open_now(),
            'last_update': timezone.now().isoformat()
        })