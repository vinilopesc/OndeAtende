"""
Modelos core simplificados para MVP OndeAtende
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings
import base64


class EncryptedField(models.TextField):
    """
    Campo criptografado para dados sensíveis (LGPD/HIPAA)
    MVP: Versão simplificada, melhorar em produção
    """

    def __init__(self, *args, **kwargs):
        kwargs['editable'] = False  # Não editável no admin por padrão
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        """Criptografa antes de salvar no banco"""
        if value is None or value == '':
            return value

        # MVP: criptografia simples com Fernet
        # Em produção: usar AWS KMS, Azure Key Vault, etc
        try:
            key = settings.ENCRYPTION_KEY.encode() if hasattr(settings, 'ENCRYPTION_KEY') else Fernet.generate_key()
            f = Fernet(key)
            encrypted = f.encrypt(str(value).encode())
            return base64.b64encode(encrypted).decode()
        except Exception:
            # Fallback: retorna texto plano (apenas para desenvolvimento)
            return value

    def from_db_value(self, value, expression, connection):
        """Descriptografa ao ler do banco"""
        if value is None or value == '':
            return value

        try:
            key = settings.ENCRYPTION_KEY.encode() if hasattr(settings, 'ENCRYPTION_KEY') else Fernet.generate_key()
            f = Fernet(key)
            encrypted = base64.b64decode(value.encode())
            return f.decrypt(encrypted).decode()
        except Exception:
            # Fallback: retorna o valor como está
            return value

    def to_python(self, value):
        """Converte para Python"""
        return value


class BaseModel(models.Model):
    """Modelo base com timestamps e UUID"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True


# Alias para compatibilidade com código existente
TrackedModel = BaseModel


class User(AbstractUser):
    """
    Usuário customizado para staff médico
    MVP: roles básicos sem complexidade de HIPAA
    """
    ROLE_CHOICES = [
        ('TRIAGE', 'Triagem'),
        ('NURSE', 'Enfermagem'),
        ('DOCTOR', 'Médico'),
        ('ADMIN', 'Admin'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='TRIAGE')
    professional_id = models.CharField(max_length=50, blank=True, help_text="CRM/COREN")

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.get_role_display()} - {self.username}"


class AuditLog(models.Model):
    """Log básico de auditoria para MVP"""
    ACTION_CHOICES = [
        ('CREATE', 'Criação'),
        ('UPDATE', 'Atualização'),
        ('DELETE', 'Exclusão'),
        ('LOGIN', 'Login'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]