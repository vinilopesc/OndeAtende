# Arquivo: apps/prefecture/serializers.py
# Criar arquivo completo:
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Prefecture, PrefectureStaff, HealthUnit, Doctor


class LoginSerializer(serializers.Serializer):
    """
    Serializer para autenticação de usuários da prefeitura.
    Valida credenciais e retorna tokens JWT.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """
        Valida as credenciais e verifica se o usuário é da prefeitura.
        """
        username = attrs.get('username')
        password = attrs.get('password')

        # Tenta autenticar com as credenciais fornecidas
        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError('Credenciais inválidas')

        # Verifica se o usuário tem perfil de prefeitura
        if not hasattr(user, 'prefecture_profile'):
            raise serializers.ValidationError('Usuário não é funcionário da prefeitura')

        if not user.is_active:
            raise serializers.ValidationError('Usuário inativo')

        # Gera tokens JWT para o usuário
        refresh = RefreshToken.for_user(user)
        profile = user.prefecture_profile

        return {
            'user': user,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'role': profile.role,
            'prefecture': {
                'id': profile.prefecture.id,
                'name': profile.prefecture.name,
                'city': profile.prefecture.city
            }
        }


class PrefectureStaffSerializer(serializers.ModelSerializer):
    """
    Serializer para funcionários da prefeitura.
    Inclui dados do usuário Django relacionado.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    prefecture_name = serializers.CharField(source='prefecture.name', read_only=True)

    class Meta:
        model = PrefectureStaff
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'department', 'phone', 'prefecture', 'prefecture_name'
        ]
        read_only_fields = ['id', 'username', 'email', 'first_name', 'last_name', 'prefecture_name']


class HealthUnitSerializer(serializers.ModelSerializer):
    """
    Serializer para unidades de saúde.
    """
    unit_type_display = serializers.CharField(source='get_unit_type_display', read_only=True)

    class Meta:
        model = HealthUnit
        fields = [
            'id', 'name', 'unit_type', 'unit_type_display',
            'cnes', 'address', 'phone', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'unit_type_display', 'created_at']

    def validate_cnes(self, value):
        """
        Valida o código CNES (deve ter pelo menos 7 dígitos).
        """
        if len(value) < 7:
            raise serializers.ValidationError("CNES deve ter pelo menos 7 dígitos")
        return value


class DoctorSerializer(serializers.ModelSerializer):
    """
    Serializer para médicos cadastrados.
    """

    class Meta:
        model = Doctor
        fields = [
            'id', 'name', 'crm', 'cpf', 'specialties',
            'phone', 'email', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_cpf(self, value):
        """
        Valida e formata o CPF (remove caracteres não numéricos).
        """
        # Remove todos os caracteres que não são dígitos
        cpf = ''.join(filter(str.isdigit, value))

        if len(cpf) != 11:
            raise serializers.ValidationError("CPF deve ter 11 dígitos")

        return cpf