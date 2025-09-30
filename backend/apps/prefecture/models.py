# Arquivo: apps/prefecture/models.py
# Criar arquivo completo:
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Prefecture(models.Model):
    """Representa uma prefeitura no sistema"""
    name = models.CharField(max_length=200, verbose_name='Nome')
    cnpj = models.CharField(max_length=18, unique=True, verbose_name='CNPJ')
    city = models.CharField(max_length=100, verbose_name='Cidade')
    state = models.CharField(max_length=2, verbose_name='Estado')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'prefectures'
        verbose_name = 'Prefeitura'
        verbose_name_plural = 'Prefeituras'
        indexes = [
            models.Index(fields=['cnpj']),
            models.Index(fields=['is_active'])
        ]

    def __str__(self):
        return f"{self.name} - {self.city}/{self.state}"


class PrefectureStaff(models.Model):
    """
    Perfil de funcionário da prefeitura.
    Estende o modelo User padrão do Django através de uma relação OneToOne.
    """
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('operator', 'Operador'),
        ('viewer', 'Visualizador')
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='prefecture_profile',
        verbose_name='Usuário'
    )
    prefecture = models.ForeignKey(
        Prefecture,
        on_delete=models.CASCADE,
        related_name='staff_members',
        verbose_name='Prefeitura'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='viewer',
        verbose_name='Papel'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    department = models.CharField(max_length=100, blank=True, verbose_name='Departamento')

    class Meta:
        db_table = 'prefecture_staff'
        verbose_name = 'Funcionário da Prefeitura'
        verbose_name_plural = 'Funcionários da Prefeitura'
        indexes = [
            models.Index(fields=['prefecture', 'user']),
            models.Index(fields=['role'])
        ]
        unique_together = [['user', 'prefecture']]  # Um usuário por prefeitura

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.prefecture.name}"


class HealthUnit(models.Model):
    """Unidades de saúde gerenciadas pela prefeitura"""
    UNIT_TYPES = [
        ('upa', 'UPA'),
        ('hospital', 'Hospital'),
        ('posto', 'Posto de Saúde'),
        ('especializado', 'Centro Especializado')
    ]

    prefecture = models.ForeignKey(
        Prefecture,
        on_delete=models.CASCADE,
        related_name='health_units',
        verbose_name='Prefeitura'
    )
    name = models.CharField(max_length=200, verbose_name='Nome')
    unit_type = models.CharField(
        max_length=20,
        choices=UNIT_TYPES,
        verbose_name='Tipo de Unidade'
    )
    cnes = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='CNES',
        help_text='Código Nacional de Estabelecimento de Saúde'
    )
    address = models.TextField(verbose_name='Endereço')
    phone = models.CharField(max_length=20, verbose_name='Telefone')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'health_units'
        verbose_name = 'Unidade de Saúde'
        verbose_name_plural = 'Unidades de Saúde'
        indexes = [
            models.Index(fields=['prefecture', 'unit_type']),
            models.Index(fields=['cnes'])
        ]

    def __str__(self):
        return f"{self.name} ({self.get_unit_type_display()})"


class Doctor(models.Model):
    """Médicos cadastrados pela prefeitura"""
    prefecture = models.ForeignKey(
        Prefecture,
        on_delete=models.CASCADE,
        related_name='doctors',
        verbose_name='Prefeitura'
    )
    name = models.CharField(max_length=200, verbose_name='Nome')
    crm = models.CharField(max_length=20, verbose_name='CRM')
    cpf = models.CharField(max_length=14, unique=True, verbose_name='CPF')
    specialties = models.JSONField(
        default=list,
        verbose_name='Especialidades',
        help_text='Lista de especialidades médicas'
    )
    phone = models.CharField(max_length=20, verbose_name='Telefone')
    email = models.EmailField(verbose_name='E-mail')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'doctors'
        verbose_name = 'Médico'
        verbose_name_plural = 'Médicos'
        indexes = [
            models.Index(fields=['prefecture', 'is_active']),
            models.Index(fields=['cpf']),
            models.Index(fields=['crm'])
        ]
        unique_together = [['crm', 'prefecture']]

    def __str__(self):
        return f"Dr(a). {self.name} - CRM: {self.crm}"