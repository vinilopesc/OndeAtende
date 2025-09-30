# apps/prefecture/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import Prefecture, PrefectureStaff, HealthUnit, Doctor


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError('Credenciais inválidas')
        if not user.is_active:
            raise serializers.ValidationError('Usuário inativo')

        refresh = RefreshToken.for_user(user)

        return {
            'user': user,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'role': user.role,
            'prefecture': {
                'id': user.prefecture.id,
                'name': user.prefecture.name,
                'city': user.prefecture.city
            }
        }


class PrefectureUserSerializer(serializers.ModelSerializer):
    prefecture_name = serializers.CharField(source='prefecture.name', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = PrefectureStaff
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'full_name', 'role', 'department', 'phone',
                  'prefecture', 'prefecture_name', 'is_active']
        read_only_fields = ['id', 'prefecture_name', 'full_name']


class HealthUnitSerializer(serializers.ModelSerializer):
    unit_type_display = serializers.CharField(source='get_unit_type_display', read_only=True)

    class Meta:
        model = HealthUnit
        fields = ['id', 'name', 'unit_type', 'unit_type_display',
                  'cnes', 'address', 'phone', 'is_active', 'created_at']

    def validate_cnes(self, value):
        if len(value) < 7:
            raise serializers.ValidationError("CNES deve ter pelo menos 7 dígitos")
        return value


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['id', 'name', 'crm', 'cpf', 'specialties',
                  'phone', 'email', 'is_active', 'created_at']

    def validate_cpf(self, value):
        # Remove caracteres não numéricos
        cpf = ''.join(filter(str.isdigit, value))
        if len(cpf) != 11:
            raise serializers.ValidationError("CPF inválido")
        return cpf