"""
Modelos core simplificados para MVP OndeAtende
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class BaseModel(models.Model):
    """Modelo base com timestamps e UUID"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True


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