# Arquivo: apps/prefecture/permissions.py
# Criar arquivo completo:
from rest_framework import permissions


class IsPrefectureStaff(permissions.BasePermission):
    """
    Permissão customizada para verificar se o usuário é funcionário da prefeitura.
    """

    def has_permission(self, request, view):
        """
        Verifica se o usuário está autenticado e tem perfil de prefeitura.
        """
        return bool(
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'prefecture_profile')
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permissão customizada que permite apenas leitura para usuários comuns
    e escrita apenas para administradores.
    """

    def has_permission(self, request, view):
        """
        Permite leitura para todos os funcionários da prefeitura,
        mas escrita apenas para administradores.
        """
        if not request.user.is_authenticated:
            return False

        if not hasattr(request.user, 'prefecture_profile'):
            return False

        # Métodos seguros (GET, HEAD, OPTIONS) são permitidos para todos
        if request.method in permissions.SAFE_METHODS:
            return True

        # Escrita apenas para administradores
        return request.user.prefecture_profile.role == 'admin'