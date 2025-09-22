# apps/facilities/models.py
"""
Modelos para gerenciamento de unidades de saúde
Inclui geolocalização, capacidade e recursos disponíveis
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.utils import timezone
from apps.core.models import TrackedModel
import math


class Facility(TrackedModel):
    """
    Unidade de Saúde com todos os recursos e capacidades
    Suporta UPA, UBS, Hospitais e Prontos-Socorros
    """
    
    FACILITY_TYPES = [
        ('UPA', 'Unidade de Pronto Atendimento'),
        ('UBS', 'Unidade Básica de Saúde'),
        ('HOSPITAL', 'Hospital'),
        ('PS', 'Pronto-Socorro'),
        ('CAPS', 'Centro de Atenção Psicossocial'),
        ('AME', 'Ambulatório Médico de Especialidades'),
    ]
    
    # Identificação
    name = models.CharField(max_length=200, db_index=True)
    official_code = models.CharField(
        max_length=20, unique=True,
        help_text="CNES - Cadastro Nacional de Estabelecimentos de Saúde"
    )
    facility_type = models.CharField(max_length=10, choices=FACILITY_TYPES)
    
    # Localização com índice espacial para buscas geográficas
    address = models.TextField()
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=2, default='MG')
    zip_code = models.CharField(max_length=9)
    
    # Coordenadas para geolocalização
    latitude = models.DecimalField(max_digits=10, decimal_places=8, db_index=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, db_index=True)
    
    # Contato
    phone_primary = models.CharField(max_length=15)
    phone_emergency = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    
    # Capacidade e Recursos
    total_beds = models.IntegerField(default=0)
    icu_beds = models.IntegerField(default=0)
    emergency_beds = models.IntegerField(default=0)
    
    # Recursos especiais disponíveis
    resources = ArrayField(
        models.CharField(max_length=50),
        default=list,
        help_text="Ex: ['tomografia', 'ressonancia', 'hemodiálise', 'uti_neo']"
    )
    
    # Especialidades atendidas
    specialties = ArrayField(
        models.CharField(max_length=50),
        default=list,
        help_text="Especialidades médicas disponíveis"
    )
    
    # Funcionamento
    is_24h = models.BooleanField(default=False)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    
    # Manchester Triage System
    manchester_enabled = models.BooleanField(default=True)
    triage_rooms = models.IntegerField(default=1)
    
    # Métricas operacionais
    average_wait_time_minutes = models.IntegerField(default=60)
    max_daily_capacity = models.IntegerField(default=100)
    
    # Status atual
    is_accepting_emergencies = models.BooleanField(default=True)
    is_accepting_walkins = models.BooleanField(default=True)
    current_occupancy_percent = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'facilities'
        verbose_name_plural = 'Facilities'
        indexes = [
            models.Index(fields=['facility_type', 'city']),
            models.Index(fields=['latitude', 'longitude']),
            GinIndex(fields=['resources']),
            GinIndex(fields=['specialties']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.facility_type})"
    
    def calculate_distance_from(self, lat: float, lng: float) -> float:
        """
        Calcula distância em KM usando fórmula de Haversine
        Essencial para encontrar unidade mais próxima
        """
        R = 6371  # Raio da Terra em KM
        
        lat1, lon1 = math.radians(float(self.latitude)), math.radians(float(self.longitude))
        lat2, lon2 = math.radians(lat), math.radians(lng)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def is_open_now(self) -> bool:
        """Verifica se a unidade está aberta agora"""
        if self.is_24h:
            return True
        
        now = timezone.localtime().time()
        
        if self.opening_time and self.closing_time:
            if self.opening_time <= self.closing_time:
                return self.opening_time <= now <= self.closing_time
            else:  # Atravessa meia-noite
                return now >= self.opening_time or now <= self.closing_time
        
        return True  # Se não tem horário definido, considera aberto
    
    def get_current_queue_status(self) -> dict:
        """
        Retorna status atual das filas por prioridade Manchester
        Usado para dashboard em tempo real
        """
        from apps.triage.models import TriageSession
        
        current_queues = {
            'RED': 0,
            'ORANGE': 0,
            'YELLOW': 0,
            'GREEN': 0,
            'BLUE': 0,
        }
        
        active_sessions = TriageSession.objects.filter(
            facility=self,
            status='WAITING',
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        )
        
        for session in active_sessions:
            current_queues[session.priority_color] += 1
        
        # Calcula tempo médio de espera por cor
        wait_times = {}
        for color in current_queues.keys():
            avg_wait = self._calculate_average_wait_time(color)
            wait_times[color] = avg_wait
        
        return {
            'queues': current_queues,
            'wait_times': wait_times,
            'total_waiting': sum(current_queues.values()),
            'critical_patients': current_queues['RED'] + current_queues['ORANGE'],
        }
    
    def _calculate_average_wait_time(self, priority_color: str) -> int:
        """Calcula tempo médio de espera para uma prioridade"""
        # Implementação simplificada - em produção usaria dados históricos
        base_times = {
            'RED': 0,
            'ORANGE': 10,
            'YELLOW': 45,
            'GREEN': 90,
            'BLUE': 180,
        }
        
        # Ajusta baseado na ocupação atual
        occupancy_factor = 1 + (self.current_occupancy_percent / 100)
        return int(base_times[priority_color] * occupancy_factor)


class FacilityResource(TrackedModel):
    """
    Recursos médicos disponíveis em tempo real
    Atualizado continuamente para gestão de capacidade
    """
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='facility_resources')
    resource_type = models.CharField(max_length=50)
    total_quantity = models.IntegerField()
    available_quantity = models.IntegerField()
    next_availability = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'facility_resources'
        unique_together = ['facility', 'resource_type']
        indexes = [
            models.Index(fields=['facility', 'available_quantity']),
        ]


class MedicalSpecialty(models.Model):
    """Especialidades médicas disponíveis"""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    requires_emergency = models.BooleanField(default=False)

    class Meta:
        db_table = 'medical_specialties'
        verbose_name_plural = 'Medical Specialties'

    def __str__(self):
        return self.name


class MedicalShift(TrackedModel):
    """Plantões médicos por unidade e especialidade"""
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='shifts')
    specialty = models.ForeignKey(MedicalSpecialty, on_delete=models.CASCADE)
    doctor = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='shifts')

    shift_date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()

    is_on_call = models.BooleanField(default=False)  # Sobreaviso
    max_appointments = models.IntegerField(default=20)
    current_appointments = models.IntegerField(default=0)

    STATUS_CHOICES = [
        ('SCHEDULED', 'Agendado'),
        ('ACTIVE', 'Em Atendimento'),
        ('COMPLETED', 'Finalizado'),
        ('CANCELLED', 'Cancelado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')

    class Meta:
        db_table = 'medical_shifts'
        unique_together = ['facility', 'doctor', 'shift_date', 'start_time']
        indexes = [
            models.Index(fields=['facility', 'shift_date', 'specialty']),
            models.Index(fields=['shift_date', 'status']),
        ]

    def __str__(self):
        return f"{self.doctor} - {self.specialty} - {self.shift_date}"

    def is_available_now(self) -> bool:
        """Verifica se plantão está ativo agora"""
        from django.utils import timezone
        now = timezone.localtime()

        if self.shift_date != now.date():
            return False

        current_time = now.time()
        return self.start_time <= current_time <= self.end_time and \
            self.status == 'ACTIVE' and \
            self.current_appointments < self.max_appointments
