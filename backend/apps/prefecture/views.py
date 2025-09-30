# Arquivo: apps/prefecture/views.py
# Criar arquivo completo (substituir tudo se já existir):
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import PrefectureStaff, HealthUnit, Doctor, Prefecture
from .serializers import (
    LoginSerializer, PrefectureStaffSerializer,
    HealthUnitSerializer, DoctorSerializer
)
from .permissions import IsPrefectureUser, IsAdminOrReadOnly


class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet para autenticação de usuários da prefeitura.
    Fornece endpoint de login que retorna tokens JWT.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """
        Autentica um usuário da prefeitura e retorna tokens de acesso.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Atualiza o último login do usuário
        user = serializer.validated_data['user']
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        return Response({
            'access': serializer.validated_data['access'],
            'refresh': serializer.validated_data['refresh'],
            'user': {
                'id': user.id,
                'username': user.username,
                'name': user.get_full_name(),
                'role': serializer.validated_data['role'],
                'prefecture': serializer.validated_data['prefecture']
            }
        })


class HealthUnitViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar unidades de saúde da prefeitura.
    Apenas usuários autenticados da prefeitura podem acessar.
    """
    serializer_class = HealthUnitSerializer
    permission_classes = [IsPrefectureUser, IsAdminOrReadOnly]

    def get_queryset(self):
        """Retorna apenas unidades da prefeitura do usuário atual"""
        profile = self.request.user.prefecture_profile
        return HealthUnit.objects.filter(
            prefecture=profile.prefecture
        ).order_by('-created_at')

    def perform_create(self, serializer):
        """Associa automaticamente a nova unidade à prefeitura do usuário"""
        profile = self.request.user.prefecture_profile
        serializer.save(prefecture=profile.prefecture)

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Retorna estatísticas agrupadas por tipo de unidade"""
        unit_type = request.query_params.get('type')
        queryset = self.get_queryset()

        if unit_type:
            queryset = queryset.filter(unit_type=unit_type)

        stats = queryset.values('unit_type').annotate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True))
        )

        return Response(stats)


class DoctorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar médicos cadastrados pela prefeitura.
    """
    serializer_class = DoctorSerializer
    permission_classes = [IsPrefectureUser, IsAdminOrReadOnly]

    def get_queryset(self):
        """Retorna apenas médicos da prefeitura do usuário atual"""
        profile = self.request.user.prefecture_profile
        return Doctor.objects.filter(
            prefecture=profile.prefecture
        ).select_related('prefecture').order_by('name')

    def perform_create(self, serializer):
        """Associa automaticamente o novo médico à prefeitura do usuário"""
        profile = self.request.user.prefecture_profile
        serializer.save(prefecture=profile.prefecture)

    @action(detail=False, methods=['get'])
    def by_specialty(self, request):
        """Filtra médicos por especialidade"""
        specialty = request.query_params.get('specialty')
        queryset = self.get_queryset()

        if specialty:
            # O campo specialties é JSONField, então usamos contains
            queryset = queryset.filter(specialties__contains=specialty)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MetricsViewSet(viewsets.GenericViewSet):
    """
    ViewSet para métricas e dashboard da prefeitura.
    """
    permission_classes = [IsPrefectureUser]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Retorna métricas consolidadas para o dashboard da prefeitura.
        """
        profile = request.user.prefecture_profile
        prefecture = profile.prefecture

        # Coleta métricas básicas do sistema
        metrics = {
            'health_units': {
                'total': HealthUnit.objects.filter(prefecture=prefecture).count(),
                'active': HealthUnit.objects.filter(
                    prefecture=prefecture,
                    is_active=True
                ).count(),
                'by_type': dict(
                    HealthUnit.objects.filter(prefecture=prefecture)
                    .values_list('unit_type')
                    .annotate(Count('id'))
                )
            },
            'doctors': {
                'total': Doctor.objects.filter(prefecture=prefecture).count(),
                'active': Doctor.objects.filter(
                    prefecture=prefecture,
                    is_active=True
                ).count()
            },
            'users': {
                'total': PrefectureStaff.objects.filter(prefecture=prefecture).count(),
                'active_today': PrefectureStaff.objects.filter(
                    prefecture=prefecture,
                    user__last_login__gte=timezone.now() - timedelta(days=1)
                ).count()
            }
        }

        return Response(metrics)