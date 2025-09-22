# apps/triage/permissions.py
"""
Sistema de permissões baseado em roles médicos
Implementa controle de acesso RBAC para conformidade HIPAA
"""

from rest_framework import permissions


class MedicalPermission(permissions.BasePermission):
    """
    Permissão customizada para staff médico
    Controla acesso baseado em role e facility
    """
    
    def has_permission(self, request, view):
        """
        Verifica permissões globais da view
        """
        # Usuário deve estar autenticado
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin tem acesso total
        if request.user.role == 'ADMIN':
            return True
        
        # Verifica se usuário está dentro do horário de trabalho
        if hasattr(request.user, 'is_within_shift'):
            if not request.user.is_within_shift():
                return False
        
        # Mapeia actions para permissões necessárias
        action_permissions = {
            'list': ['view_queue'],
            'retrieve': ['view_patient'],
            'create': ['create_triage'],
            'update': ['update_triage'],
            'partial_update': ['update_triage'],
            'destroy': ['delete_triage'],
            'queue': ['view_queue'],
            'call_patient': ['call_patient'],
            'discharge': ['discharge_patient'],
            'statistics': ['view_analytics'],
            'medical_history': ['view_medical_history'],
        }
        
        # Obtém action atual
        action = getattr(view, 'action', None)
        if action and action in action_permissions:
            required_permissions = action_permissions[action]
            
            # Verifica se usuário tem alguma das permissões necessárias
            for perm in required_permissions:
                if request.user.has_permission(perm):
                    return True
            
            return False
        
        # Default: permite leitura, nega escrita
        return request.method in permissions.SAFE_METHODS
    
    def has_object_permission(self, request, view, obj):
        """
        Verifica permissões específicas do objeto
        """
        # Admin tem acesso total
        if request.user.role == 'ADMIN':
            return True
        
        # Verifica se objeto pertence à facility do usuário
        if hasattr(obj, 'facility'):
            if obj.facility != request.user.facility:
                return False
        
        # Verifica se é paciente da facility do usuário
        if hasattr(obj, 'triage_sessions'):
            user_facility = request.user.facility
            if not obj.triage_sessions.filter(facility=user_facility).exists():
                return False
        
        # Para TriageSession, verifica status e role
        if hasattr(obj, 'status') and hasattr(obj, 'priority_color'):
            # Apenas TRIAGE_NURSE pode modificar triagem em andamento
            if obj.status == 'TRIAGE' and request.user.role != 'TRIAGE_NURSE':
                return request.method in permissions.SAFE_METHODS
            
            # Apenas DOCTOR pode dar alta
            if obj.status == 'IN_CARE' and request.user.role != 'DOCTOR':
                return request.method in permissions.SAFE_METHODS
        
        return True


class PublicReadOnly(permissions.BasePermission):
    """
    Permite apenas leitura pública
    Usado para endpoints informativos
    """
    
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permite edição apenas para o próprio usuário
    """
    
    def has_object_permission(self, request, view, obj):
        # Leitura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escrita apenas para o owner
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class EmergencyOverride(permissions.BasePermission):
    """
    Permissão especial para situações de emergência
    Permite acesso expandido para casos RED/ORANGE
    """
    
    def has_object_permission(self, request, view, obj):
        # Em emergências (RED/ORANGE), permite acesso expandido
        if hasattr(obj, 'priority_color'):
            if obj.priority_color in ['RED', 'ORANGE']:
                # Qualquer médico ou enfermeiro pode acessar
                if request.user.role in ['DOCTOR', 'TRIAGE_NURSE', 'NURSE']:
                    return True
        
        return False
