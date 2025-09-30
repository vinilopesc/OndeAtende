# apps/triage/models.py
"""
Modelos para sistema de triagem Manchester
Gerencia todo o fluxo desde chegada até atendimento
"""

from django.db import models
from apps.core.models import TrackedModel, EncryptedField
from apps.facilities.models import Facility
from apps.triage.manchester import TriagePriority
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Patient(TrackedModel):
    """
    Dados do paciente com proteção LGPD/HIPAA
    Campos sensíveis são criptografados
    """

    # Identificação (criptografada para PHI)
    cpf = EncryptedField(unique=True, help_text="CPF criptografado")
    sus_number = EncryptedField(null=True, blank=True, help_text="Cartão SUS")

    # Dados demográficos básicos
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    gender = models.CharField(max_length=1, choices=[
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
    ])

    # Contato (criptografado)
    phone = EncryptedField()
    email = EncryptedField(null=True, blank=True)
    address = EncryptedField(null=True, blank=True)

    # Informações médicas relevantes
    blood_type = models.CharField(max_length=3, blank=True, choices=[
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ])
    allergies = models.JSONField(default=list)
    chronic_conditions = models.JSONField(default=dict)
    current_medications = models.JSONField(default=list)

    # Contato de emergência
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = EncryptedField()
    emergency_contact_relationship = models.CharField(max_length=50)

    # Preferências
    preferred_language = models.CharField(max_length=5, default='pt-BR')
    needs_accessibility = models.BooleanField(default=False)
    accessibility_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'patients'
        indexes = [
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['birth_date']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self) -> int:
        """Calcula idade do paciente"""
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @property
    def age_months(self) -> int:
        """Idade em meses (importante para pediatria)"""
        from datetime import date
        today = date.today()
        months = (today.year - self.birth_date.year) * 12
        months += today.month - self.birth_date.month
        if today.day < self.birth_date.day:
            months -= 1
        return months


class TriageSession(TrackedModel):
    """
    Sessão de triagem Manchester completa
    Rastreia todo o fluxo do paciente
    """

    STATUS_CHOICES = [
        ('ARRIVAL', 'Chegada'),
        ('TRIAGE', 'Em Triagem'),
        ('WAITING', 'Aguardando Atendimento'),
        ('IN_CARE', 'Em Atendimento'),
        ('OBSERVATION', 'Em Observação'),
        ('DISCHARGED', 'Alta'),
        ('TRANSFERRED', 'Transferido'),
        ('LEFT', 'Deixou a Unidade'),
    ]

    # Identificação única da sessão
    session_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Relações principais
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='triage_sessions')
    facility = models.ForeignKey(Facility, on_delete=models.PROTECT, related_name='triage_sessions')
    triage_nurse = models.ForeignKey('core.User', on_delete=models.PROTECT, null=True, related_name='triages_performed')

    # Timestamps do fluxo
    arrival_time = models.DateTimeField(auto_now_add=True)
    triage_start_time = models.DateTimeField(null=True, blank=True)
    triage_end_time = models.DateTimeField(null=True, blank=True)
    called_time = models.DateTimeField(null=True, blank=True)
    attendance_start_time = models.DateTimeField(null=True, blank=True)
    discharge_time = models.DateTimeField(null=True, blank=True)

    # Queixa principal e sintomas
    chief_complaint = models.CharField(max_length=100)
    complaint_description = models.TextField()
    symptom_duration_hours = models.IntegerField(null=True, blank=True)
    pain_scale = models.IntegerField(null=True, blank=True, validators=[
        MinValueValidator(0),
        MaxValueValidator(10)
    ])

    # Manchester Triage
    manchester_flowchart = models.CharField(max_length=50)
    discriminators_answered = models.JSONField(default=dict)
    priority_color = models.CharField(max_length=10, choices=[
        ('RED', 'Vermelho'),
        ('ORANGE', 'Laranja'),
        ('YELLOW', 'Amarelo'),
        ('GREEN', 'Verde'),
        ('BLUE', 'Azul'),
    ])
    priority_level = models.IntegerField()  # 1-5
    priority_reason = models.TextField()

    # Sinais vitais na triagem
    vital_signs = models.JSONField(default=dict)
    # Estrutura: {
    #     'blood_pressure_systolic': 120,
    #     'blood_pressure_diastolic': 80,
    #     'heart_rate': 72,
    #     'respiratory_rate': 16,
    #     'temperature': 36.5,
    #     'spo2': 98,
    #     'glucose': 95,
    #     'gcs': 15,
    #     'pain_scale': 5
    # }

    # Status e posição na fila
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ARRIVAL')
    queue_position = models.IntegerField(null=True, blank=True)
    estimated_wait_minutes = models.IntegerField(null=True, blank=True)

    # Override clínico (quando enfermeiro ajusta prioridade)
    clinical_override = models.BooleanField(default=False)
    override_reason = models.TextField(blank=True)
    override_by = models.ForeignKey('core.User', on_delete=models.PROTECT, null=True, blank=True, related_name='+')

    # Notas e observações
    triage_notes = models.TextField(blank=True)
    medical_notes = models.TextField(blank=True)

    # Dados para analytics
    total_wait_time_minutes = models.IntegerField(null=True, blank=True)
    door_to_triage_minutes = models.IntegerField(null=True, blank=True)
    triage_to_attendance_minutes = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'triage_sessions'
        ordering = ['priority_level', 'arrival_time']
        indexes = [
            models.Index(fields=['facility', 'status', 'priority_level']),
            models.Index(fields=['patient', 'arrival_time']),
            models.Index(fields=['session_uuid']),
            models.Index(fields=['arrival_time', 'priority_color']),
        ]

    def __str__(self):
        return f"{self.patient} - {self.get_priority_color_display()} - {self.arrival_time:%d/%m %H:%M}"

    def calculate_queue_position(self) -> int:
        """
        Calcula posição na fila baseado em Manchester
        Pacientes com mesma prioridade são ordenados por chegada
        """
        from django.db.models import Q

        return TriageSession.objects.filter(
            Q(facility=self.facility) &
            Q(status='WAITING') &
            (
                    Q(priority_level__lt=self.priority_level) |
                    Q(
                        priority_level=self.priority_level,
                        arrival_time__lt=self.arrival_time
                    )
            )
        ).count() + 1

    def update_wait_time_estimate(self) -> int:
        """
        Estima tempo de espera baseado em dados históricos
        e situação atual da unidade
        """
        # Busca pacientes na frente
        ahead_count = self.calculate_queue_position() - 1

        # Tempo médio por prioridade (em minutos)
        avg_times = {
            1: 5,  # RED
            2: 15,  # ORANGE
            3: 30,  # YELLOW
            4: 45,  # GREEN
            5: 60,  # BLUE
        }

        # Calcula estimativa
        base_time = avg_times.get(self.priority_level, 30)
        estimated_wait = ahead_count * base_time

        # Ajusta baseado na ocupação da unidade
        if self.facility.current_occupancy_percent > 90:
            estimated_wait = int(estimated_wait * 1.5)

        self.estimated_wait_minutes = estimated_wait
        self.save(update_fields=['estimated_wait_minutes'])

        return estimated_wait

    def get_recommendations(self) -> list:
        """Retorna recomendações baseadas na prioridade"""
        from apps.triage.manchester import ManchesterTriageSystem

        mts = ManchesterTriageSystem()
        priority = TriagePriority[self.priority_color]

        return mts._generate_recommendations(
            priority,
            self.manchester_flowchart,
            self.priority_reason,
            self.vital_signs
        )


class TriageAuditLog(models.Model):
    """
    Log específico para auditoria de decisões de triagem
    Requisito médico-legal para rastrear todas as decisões
    """
    session = models.ForeignKey(TriageSession, on_delete=models.CASCADE, related_name='audit_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50)
    performed_by = models.ForeignKey('core.User', on_delete=models.PROTECT)
    details = models.JSONField()

    class Meta:
        db_table = 'triage_audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['session', 'timestamp']),
        ]