# apps/core/views.py
"""
Views principais do sistema
Inclui healthcheck, autenticação e endpoints de sistema
"""

from django.http import JsonResponse
from django.utils import timezone
from django.db import connection
from django.core.cache import cache
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import authenticate, login, logout
import logging

logger = logging.getLogger(__name__)


def healthz(request):
    """
    Healthcheck endpoint para monitoramento
    Verifica conectividade com banco e cache
    """
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['checks']['database'] = 'error'
        health_status['status'] = 'unhealthy'
        logger.error(f"Database health check failed: {e}")
    
    # Check cache
    try:
        cache.set('health_check', 'ok', 1)
        if cache.get('health_check') == 'ok':
            health_status['checks']['cache'] = 'ok'
        else:
            health_status['checks']['cache'] = 'error'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['cache'] = 'error'
        health_status['status'] = 'unhealthy'
        logger.error(f"Cache health check failed: {e}")
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)


class CustomAuthToken(ObtainAuthToken):
    """
    Endpoint customizado de autenticação
    Retorna token + informações do usuário
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        # Log de acesso para auditoria
        logger.info(f"Login successful: {user.username} from {request.META.get('REMOTE_ADDR')}")
        
        # Atualiza último acesso
        user.last_login = timezone.now()
        user.failed_login_attempts = 0
        user.save(update_fields=['last_login', 'failed_login_attempts'])
        
        return Response({
            'token': token.key,
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'facility': {
                    'id': str(user.facility.id) if user.facility else None,
                    'name': user.facility.name if user.facility else None,
                } if user.facility else None,
                'permissions': self._get_user_permissions(user),
            }
        })
    
    def _get_user_permissions(self, user):
        """Retorna lista de permissões do usuário baseado no role"""
        role_permissions = {
            'ADMIN': ['all'],
            'DOCTOR': [
                'view_all', 'create_prescription', 'discharge_patient',
                'view_medical_history', 'update_medical_record'
            ],
            'TRIAGE_NURSE': [
                'create_triage', 'view_queue', 'update_vitals',
                'call_patient', 'view_patient'
            ],
            'NURSE': [
                'view_queue', 'update_vitals', 'view_patient'
            ],
            'COORDINATOR': [
                'view_analytics', 'manage_staff', 'view_all',
                'generate_reports'
            ],
            'RECEPTIONIST': [
                'view_queue', 'register_patient', 'call_patient'
            ],
        }
        
        return role_permissions.get(user.role, [])


@api_view(['POST'])
def logout_view(request):
    """
    Logout endpoint
    Remove token e registra saída
    """
    if request.user.is_authenticated:
        # Remove token
        try:
            token = Token.objects.get(user=request.user)
            token.delete()
        except Token.DoesNotExist:
            pass
        
        # Log de auditoria
        logger.info(f"Logout: {request.user.username}")
        
        # Django logout
        logout(request)
    
    return Response({
        'message': 'Logout realizado com sucesso'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def current_user(request):
    """
    Retorna informações do usuário atual
    """
    if not request.user.is_authenticated:
        return Response({
            'error': 'Não autenticado'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    user = request.user
    return Response({
        'id': str(user.id),
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role,
        'professional_id': user.professional_id,
        'facility': {
            'id': str(user.facility.id) if user.facility else None,
            'name': user.facility.name if user.facility else None,
            'type': user.facility.facility_type if user.facility else None,
        } if user.facility else None,
        'shift': {
            'start': user.shift_start.isoformat() if user.shift_start else None,
            'end': user.shift_end.isoformat() if user.shift_end else None,
        },
        'is_within_shift': user.is_within_shift() if hasattr(user, 'is_within_shift') else True,
    })


@api_view(['POST'])
@api_view(['POST'])
def change_password(request):
    """
    Endpoint para trocar senha
    Requer senha atual
    """
    if not request.user.is_authenticated:
        return Response({
            'error': 'Não autenticado'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    
    if not current_password or not new_password:
        return Response({
            'error': 'Senha atual e nova são obrigatórias'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verifica senha atual
    if not request.user.check_password(current_password):
        return Response({
            'error': 'Senha atual incorreta'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validação de senha nova
    if len(new_password) < 8:
        return Response({
            'error': 'Nova senha deve ter no mínimo 8 caracteres'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Atualiza senha
    request.user.set_password(new_password)
    request.user.last_password_change = timezone.now()
    request.user.save()
    
    # Remove token antigo
    Token.objects.filter(user=request.user).delete()
    
    # Cria novo token
    token = Token.objects.create(user=request.user)
    
    logger.info(f"Password changed: {request.user.username}")
    
    return Response({
        'message': 'Senha alterada com sucesso',
        'token': token.key
    })