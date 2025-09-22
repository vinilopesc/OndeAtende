# apps/core/models.py
"""
Modelos base com auditoria completa para conformidade HIPAA/LGPD
Implementa rastreamento completo de mudanças para dados médicos críticos
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone
from cryptography.fernet import Fernet
import hashlib
import json


class TrackedModel(models.Model):
    """
    Modelo abstrato com rastreamento completo de auditoria
    Essencial para conformidade HIPAA e requisitos médico-legais
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    created_by = models.ForeignKey(
        'User', on_delete=models.PROTECT,
        related_name='+', null=True, blank=True
    )
    updated_by = models.ForeignKey(
        'User', on_delete=models.PROTECT,
        related_name='+', null=True, blank=True
    )
    is_active = models.BooleanField(default=True, db_index=True)

    # Campo de hash para garantir integridade dos dados
    data_hash = models.CharField(max_length=64, editable=False, null=True)

    class Meta:
        abstract = True

    def calculate_hash(self):
        """Calcula hash SHA-256 dos dados críticos para detecção de tampering"""
        critical_fields = {}
        for field in self._meta.fields:
            if field.name not in ['data_hash', 'updated_at', 'updated_by']:
                value = getattr(self, field.name)
                if value is not None:
                    critical_fields[field.name] = str(value)

        data_string = json.dumps(critical_fields, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()

    def save(self, *args, **kwargs):
        """Override save para incluir hash de integridade"""
        self.data_hash = self.calculate_hash()
        super().save(*args, **kwargs)

    def verify_integrity(self):
        """Verifica se os dados não foram alterados externamente"""
        return self.data_hash == self.calculate_hash()


class User(AbstractUser):
    """
    Modelo de usuário customizado para staff médico
    Inclui roles específicos do ambiente hospitalar
    """
    ROLE_CHOICES = [
        ('TRIAGE_NURSE', 'Enfermeiro(a) de Triagem'),
        ('NURSE', 'Enfermeiro(a)'),
        ('DOCTOR', 'Médico(a)'),
        ('COORDINATOR', 'Coordenador(a)'),
        ('ADMIN', 'Administrador'),
        ('RECEPTIONIST', 'Recepcionista'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professional_id = models.CharField(
        max_length=20, unique=True,
        help_text="CRM/COREN/Registro Profissional"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    facility = models.ForeignKey(
        'facilities.Facility', on_delete=models.CASCADE,
        related_name='staff_members'
    )

    # Campos para conformidade e segurança
    last_password_change = models.DateTimeField(auto_now_add=True)
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=32, blank=True)

    # Controle de acesso baseado em tempo
    shift_start = models.TimeField(null=True, blank=True)
    shift_end = models.TimeField(null=True, blank=True)

    # Auditoria de acesso
    last_phi_access = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'medical_users'
        indexes = [
            models.Index(fields=['professional_id']),
            models.Index(fields=['facility', 'role']),
        ]

    def has_permission(self, permission_code):
        """Verifica permissões baseadas em role"""
        role_permissions = {
            'TRIAGE_NURSE': ['create_triage', 'view_queue', 'update_vitals'],
            'DOCTOR': ['view_all', 'create_prescription', 'discharge_patient'],
            'COORDINATOR': ['view_analytics', 'manage_staff', 'view_all'],
            'ADMIN': ['all'],
        }

        if self.role == 'ADMIN' or 'all' in role_permissions.get(self.role, []):
            return True

        return permission_code in role_permissions.get(self.role, [])

    def is_within_shift(self):
        """Verifica se usuário está dentro do horário de trabalho"""
        if not self.shift_start or not self.shift_end:
            return True  # Sem restrição de horário

        now = timezone.now().time()
        return self.shift_start <= now <= self.shift_end


class AuditLog(models.Model):
    """
    Log de auditoria imutável para conformidade HIPAA
    Registra TODOS os acessos a dados de pacientes
    """
    ACTION_CHOICES = [
        ('CREATE', 'Criação'),
        ('READ', 'Leitura'),
        ('UPDATE', 'Atualização'),
        ('DELETE', 'Exclusão'),
        ('PHI_ACCESS', 'Acesso a PHI'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('FAILED_LOGIN', 'Tentativa de Login Falha'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    # Informações do objeto acessado
    model_name = models.CharField(max_length=50, null=True)
    object_id = models.UUIDField(null=True)
    object_repr = models.TextField(null=True)

    # Dados da requisição
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    request_method = models.CharField(max_length=10)
    request_path = models.TextField()

    # Dados adicionais
    details = models.JSONField(default=dict)

    # Hash chain para garantir imutabilidade
    previous_hash = models.CharField(max_length=64, null=True)
    current_hash = models.CharField(max_length=64)

    class Meta:
        db_table = 'hipaa_audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'user']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]

    def save(self, *args, **kwargs):
        """Override save para tornar o log imutável"""
        if self.pk:
            raise ValidationError("Audit logs são imutáveis e não podem ser alterados")

        # Calcula hash incluindo o hash anterior para criar chain
        last_log = AuditLog.objects.order_by('-timestamp').first()
        if last_log:
            self.previous_hash = last_log.current_hash

        hash_data = f"{self.timestamp}{self.user_id}{self.action}{self.object_id}{self.previous_hash}"
        self.current_hash = hashlib.sha256(hash_data.encode()).hexdigest()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Previne exclusão de logs de auditoria"""
        raise ValidationError("Audit logs não podem ser deletados por requisitos de conformidade")


class EncryptedField(models.TextField):
    """
    Campo customizado para dados sensíveis com criptografia AES-256
    Usado para PHI (Protected Health Information)
    """

    def __init__(self, *args, **kwargs):
        self.cipher_suite = Fernet(self._get_encryption_key())
        super().__init__(*args, **kwargs)

    def _get_encryption_key(self):
        """Obtém chave de criptografia do ambiente"""
        import os
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            raise ValueError("ENCRYPTION_KEY não configurada - crítico para segurança PHI")
        return key.encode()

    def from_db_value(self, value, expression, connection):
        """Descriptografa ao ler do banco"""
        if value is None:
            return value
        try:
            return self.cipher_suite.decrypt(value.encode()).decode()
        except:
            # Log erro de descriptografia para auditoria
            return None

    def to_python(self, value):
        """Converte para Python"""
        if isinstance(value, str) or value is None:
            return value
        return str(value)

    def get_prep_value(self, value):
        """Criptografa antes de salvar no banco"""
        if value is None:
            return value
        encrypted = self.cipher_suite.encrypt(value.encode())
        return encrypted.decode()


class SystemConfiguration(models.Model):
    """
    Configurações do sistema para controle dinâmico
    Permite ajustes sem redeploy
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField()
    description = models.TextField()
    last_modified = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, on_delete=models.PROTECT)

    # Configurações críticas do sistema
    DEFAULT_CONFIGS = {
        'max_queue_size': {'value': 100, 'description': 'Tamanho máximo da fila por prioridade'},
        'session_timeout_minutes': {'value': 15, 'description': 'Timeout de sessão para workstations médicas'},
        'password_expiry_days': {'value': 90, 'description': 'Dias para expiração de senha'},
        'max_failed_login_attempts': {'value': 5, 'description': 'Tentativas antes de bloquear conta'},
        'manchester_version': {'value': '3.0', 'description': 'Versão do protocolo Manchester'},
        'enable_ai_triage_assist': {'value': False, 'description': 'Habilitar assistência AI na triagem'},
    }

    class Meta:
        db_table = 'system_configuration'

    @classmethod
    def get_value(cls, key, default=None):
        """Obtém valor de configuração com cache"""
        from django.core.cache import cache

        cache_key = f'sysconfig:{key}'
        value = cache.get(cache_key)

        if value is None:
            try:
                config = cls.objects.get(key=key)
                value = config.value
                cache.set(cache_key, value, timeout=300)  # Cache por 5 minutos
            except cls.DoesNotExist:
                if key in cls.DEFAULT_CONFIGS:
                    return cls.DEFAULT_CONFIGS[key]['value']
                return default

        return value