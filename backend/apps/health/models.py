from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class ManchesterProtocol(models.TextChoices):
    RED = 'RED', 'Vermelho - Emergência'
    ORANGE = 'ORANGE', 'Laranja - Muito Urgente'
    YELLOW = 'YELLOW', 'Amarelo - Urgente'
    GREEN = 'GREEN', 'Verde - Pouco Urgente'
    BLUE = 'BLUE', 'Azul - Não Urgente'


class Symptom(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    base_priority = models.CharField(
        max_length=10,
        choices=ManchesterProtocol.choices
    )
    keywords = models.TextField(help_text="Palavras-chave separadas por vírgula")

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['base_priority']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_base_priority_display()})"


class MedicalShift(models.Model):
    upa = models.ForeignKey('UPA', on_delete=models.CASCADE, related_name='shifts')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shifts')
    specialty = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    max_consultations = models.IntegerField(default=20)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['upa', 'start_time']),
            models.Index(fields=['doctor', 'is_active']),
        ]

    def __str__(self):
        return f"{self.doctor.get_full_name()} - {self.upa.name} ({self.start_time:%d/%m %H:%M})"


class Triage(models.Model):
    STATUS_CHOICES = [
        ('WAITING', 'Aguardando'),
        ('IN_TRIAGE', 'Em Triagem'),
        ('TRIAGED', 'Triado'),
        ('IN_CONSULTATION', 'Em Consulta'),
        ('COMPLETED', 'Finalizado'),
    ]

    patient_name = models.CharField(max_length=200)
    patient_cpf = models.CharField(max_length=14)
    patient_phone = models.CharField(max_length=20)
    patient_age = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(150)])

    upa = models.ForeignKey('UPA', on_delete=models.CASCADE, related_name='triages')
    symptoms = models.ManyToManyField(Symptom, related_name='triages')
    main_complaint = models.TextField()

    # Vital signs
    blood_pressure = models.CharField(max_length=10, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    oxygen_saturation = models.IntegerField(null=True, blank=True)
    pain_level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        null=True, blank=True
    )

    priority = models.CharField(
        max_length=10,
        choices=ManchesterProtocol.choices,
        db_index=True
    )
    priority_reason = models.TextField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='WAITING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    triaged_at = models.DateTimeField(null=True, blank=True)
    called_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    assigned_shift = models.ForeignKey(
        MedicalShift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultations'
    )

    class Meta:
        ordering = ['priority', 'created_at']
        indexes = [
            models.Index(fields=['upa', 'status', 'priority']),
            models.Index(fields=['patient_cpf']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.patient_name} - {self.get_priority_display()} ({self.created_at:%d/%m %H:%M})"

    def calculate_priority(self):
        """Calcula prioridade baseada em sintomas e sinais vitais"""
        # Critérios críticos que definem emergência
        if any([
            self.pain_level and self.pain_level >= 9,
            self.oxygen_saturation and self.oxygen_saturation < 90,
            self.heart_rate and (self.heart_rate < 40 or self.heart_rate > 150),
            self.temperature and self.temperature > 39.5,
        ]):
            return ManchesterProtocol.RED

        # Baseado nos sintomas mais graves
        if self.symptoms.exists():
            worst_priority = min(
                self.symptoms.values_list('base_priority', flat=True),
                key=lambda x: list(ManchesterProtocol.values).index(x)
            )
            return worst_priority

        return ManchesterProtocol.GREEN