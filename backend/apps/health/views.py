from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Symptom, MedicalShift, Triage, ManchesterProtocol
from .serializers import (
    SymptomSerializer, MedicalShiftSerializer,
    TriageCreateSerializer, TriageDetailSerializer
)


class SymptomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Symptom.objects.all()
    serializer_class = SymptomSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Busca sintomas por palavra-chave"""
        query = request.query_params.get('q', '')
        if len(query) < 3:
            return Response([])

        symptoms = self.queryset.filter(
            Q(name__icontains=query) |
            Q(keywords__icontains=query)
        )[:10]

        serializer = self.get_serializer(symptoms, many=True)
        return Response(serializer.data)


class MedicalShiftViewSet(viewsets.ModelViewSet):
    queryset = MedicalShift.objects.select_related('upa', 'doctor')
    serializer_class = MedicalShiftSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()

        # Filtros
        upa_id = self.request.query_params.get('upa')
        if upa_id:
            qs = qs.filter(upa_id=upa_id)

        # Apenas turnos ativos do dia
        today = timezone.now().date()
        qs = qs.filter(
            is_active=True,
            start_time__date__gte=today
        )

        return qs.annotate(
            consultations_count=Count('consultations')
        ).order_by('start_time')

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Retorna escalas ativas no momento"""
        now = timezone.now()
        shifts = self.queryset.filter(
            is_active=True,
            start_time__lte=now,
            end_time__gte=now
        )
        serializer = self.get_serializer(shifts, many=True)
        return Response(serializer.data)


class TriageViewSet(viewsets.ModelViewSet):
    queryset = Triage.objects.select_related('upa').prefetch_related('symptoms')
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return TriageCreateSerializer
        return TriageDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # Filtros
        upa_id = self.request.query_params.get('upa')
        if upa_id:
            qs = qs.filter(upa_id=upa_id)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Para cidadão, mostrar apenas suas triagens
        cpf = self.request.query_params.get('cpf')
        if cpf:
            qs = qs.filter(patient_cpf=cpf)

        return qs

    @action(detail=False, methods=['get'])
    def queue_status(self, request):
        """Status da fila por UPA e prioridade"""
        upa_id = request.query_params.get('upa')
        if not upa_id:
            return Response(
                {"error": "UPA é obrigatória"},
                status=status.HTTP_400_BAD_REQUEST
            )

        queue_data = {}
        for priority in ManchesterProtocol.values:
            count = self.queryset.filter(
                upa_id=upa_id,
                status='TRIAGED',
                priority=priority
            ).count()

            queue_data[priority] = {
                'label': ManchesterProtocol[priority].label,
                'count': count,
                'estimated_wait': self._calculate_wait_time(priority, count)
            }

        return Response(queue_data)

    def _calculate_wait_time(self, priority, queue_size):
        base_times = {
            'RED': 0,
            'ORANGE': 10,
            'YELLOW': 60,
            'GREEN': 120,
            'BLUE': 240
        }
        return base_times.get(priority, 120) + (queue_size * 15)

    @action(detail=True, methods=['post'])
    def call_patient(self, request, pk=None):
        """Chama paciente para atendimento"""
        triage = self.get_object()

        if triage.status != 'TRIAGED':
            return Response(
                {"error": "Paciente não está aguardando"},
                status=status.HTTP_400_BAD_REQUEST
            )

        triage.status = 'IN_CONSULTATION'
        triage.called_at = timezone.now()
        triage.save()

        serializer = self.get_serializer(triage)
        return Response(serializer.data)