# apps/triage/views.py
"""
ViewSets para API REST do sistema de triagem
Implementa endpoints com permissões médicas apropriadas
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
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


class PublicTriageViewSet(viewsets.GenericViewSet):
    """
    ViewSet público para auto-triagem de pacientes
    Não requer autenticação
    """
    permission_classes = [AllowAny]
    serializer_class = TriageSessionSerializer
    
    @action(detail=False, methods=['post'])
    def self_triage(self, request):
        """
        Endpoint público para auto-triagem
        Paciente responde questionário e recebe orientações
        """
        # Extrai dados do request
        complaint = request.data.get('complaint')
        discriminators = request.data.get('discriminators', {})
        vital_signs = request.data.get('vital_signs', {})
        patient_age = request.data.get('age')
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        
        if not complaint:
            return Response(
                {'error': 'Queixa principal é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calcula prioridade usando Manchester
        from apps.triage.manchester import ManchesterTriageSystem
        mts = ManchesterTriageSystem()
        
        # Converte idade para meses se fornecida
        age_months = None
        if patient_age:
            age_months = int(patient_age * 12) if patient_age < 18 else None
        
        priority, reason, recommendations = mts.calculate_priority(
            complaint=complaint,
            discriminator_answers=discriminators,
            vital_signs=vital_signs,
            patient_age_months=age_months
        )
        
        # Busca unidades recomendadas se coordenadas fornecidas
        recommended_facilities = []
        if lat and lng:
            from apps.triage.routing import TriageRouter
            router = TriageRouter()
            
            # Cria sessão temporária para roteamento
            temp_session = TriageSession(
                manchester_flowchart=complaint,
                discriminators_answered=discriminators,
                priority_color=priority.name,
                priority_level=priority.value[0],
                priority_reason=reason,
                vital_signs=vital_signs
            )
            
            recommended_facilities = router.route_patient(
                temp_session,
                float(lat),
                float(lng),
                max_results=3
            )
        
        # Prepara resposta
        response_data = {
            'priority': {
                'color': priority.name,
                'level': priority.value[0],
                'max_wait_minutes': priority.value[1],
                'display_name': priority.value[2]
            },
            'reason': reason,
            'recommendations': recommendations,
            'recommended_facilities': recommended_facilities,
            'emergency_phone': '192' if priority.name in ['RED', 'ORANGE'] else None,
            'timestamp': timezone.now().isoformat()
        }
        
        # Log para analytics (anonimizado)
        logger.info(f"Auto-triagem: {priority.name} - {complaint}")
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def flowcharts(self, request):
        """Lista todos os fluxogramas Manchester disponíveis"""
        from apps.triage.manchester import ManchesterTriageSystem
        mts = ManchesterTriageSystem()
        
        flowcharts = []
        for key, flowchart in mts.flowcharts.items():
            flowcharts.append({
                'id': key,
                'name': flowchart.name,
                'description': flowchart.description,
                'age_specific': flowchart.age_specific,
                'obstetric_specific': flowchart.obstetric_specific,
                'discriminator_count': len(flowchart.discriminators)
            })
        
        return Response(flowcharts)


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
    
    @action(detail=True, methods=['post'])
    def get_routing(self, request, pk=None):
        """
        Obtém roteamento otimizado pós-triagem
        Body: {lat: float, lng: float}
        """
        session = self.get_object()
        
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        
        if not lat or not lng:
            return Response(
                {'error': 'Coordenadas (lat, lng) são obrigatórias'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.triage.routing import TriageRouter
        router = TriageRouter()
        
        facilities = router.route_patient(
            session,
            float(lat),
            float(lng),
            max_results=3
        )
        
        # Salva recomendação no banco
        session.triage_notes += f"\n\nUnidades recomendadas: {[f['facility']['name'] for f in facilities]}"
        session.save()
        
        return Response({
            'session_id': str(session.id),
            'priority': session.priority_color,
            'priority_reason': session.priority_reason,
            'recommended_facilities': facilities,
            'emergency_message': self._get_emergency_message(session.priority_color)
        })
    
    def _get_emergency_message(self, priority: str):
        """Mensagem de emergência baseada na prioridade"""
        if priority == 'RED':
            return "EMERGÊNCIA MÉDICA! Ligue 192 IMEDIATAMENTE ou vá ao hospital mais próximo!"
        elif priority == 'ORANGE':
            return "Situação muito urgente. Procure atendimento em até 10 minutos."
        return None
    
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
    permission_classes = [AllowAny]  # Público pode ver unidades
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