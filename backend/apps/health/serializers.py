from rest_framework import serializers
from .models import Symptom, MedicalShift, Triage, UPA


class SymptomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symptom
        fields = '__all__'


class MedicalShiftSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    upa_name = serializers.CharField(source='upa.name', read_only=True)
    available_slots = serializers.SerializerMethodField()

    class Meta:
        model = MedicalShift
        fields = '__all__'
        read_only_fields = ['doctor_name', 'upa_name', 'available_slots']

    def get_available_slots(self, obj):
        used = obj.consultations.filter(status__in=['TRIAGED', 'IN_CONSULTATION']).count()
        return obj.max_consultations - used


class TriageCreateSerializer(serializers.ModelSerializer):
    symptoms_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Triage
        fields = [
            'patient_name', 'patient_cpf', 'patient_phone', 'patient_age',
            'upa', 'main_complaint', 'symptoms_ids',
            'blood_pressure', 'heart_rate', 'temperature',
            'oxygen_saturation', 'pain_level'
        ]

    def validate_patient_cpf(self, value):
        # Remove formatação
        cpf = ''.join(filter(str.isdigit, value))
        if len(cpf) != 11:
            raise serializers.ValidationError("CPF inválido")
        return cpf

    def create(self, validated_data):
        symptoms_ids = validated_data.pop('symptoms_ids', [])
        triage = Triage.objects.create(**validated_data)

        if symptoms_ids:
            triage.symptoms.set(symptoms_ids)

        # Calcula prioridade automaticamente
        triage.priority = triage.calculate_priority()
        triage.priority_reason = self._generate_priority_reason(triage)
        triage.save()

        return triage

    def _generate_priority_reason(self, triage):
        reasons = []
        if triage.pain_level and triage.pain_level >= 7:
            reasons.append(f"Dor intensa ({triage.pain_level}/10)")
        if triage.temperature and triage.temperature > 38:
            reasons.append(f"Febre ({triage.temperature}°C)")
        if triage.symptoms.exists():
            symptom_names = triage.symptoms.values_list('name', flat=True)[:3]
            reasons.append(f"Sintomas: {', '.join(symptom_names)}")
        return " | ".join(reasons) or "Avaliação inicial"


class TriageDetailSerializer(serializers.ModelSerializer):
    symptoms = SymptomSerializer(many=True, read_only=True)
    upa_name = serializers.CharField(source='upa.name', read_only=True)
    wait_time = serializers.SerializerMethodField()
    position_in_queue = serializers.SerializerMethodField()

    class Meta:
        model = Triage
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'priority', 'priority_reason']

    def get_wait_time(self, obj):
        if obj.status in ['COMPLETED', 'IN_CONSULTATION']:
            return 0

        # Estimativa baseada na prioridade
        wait_times = {
            'RED': 0,
            'ORANGE': 10,
            'YELLOW': 60,
            'GREEN': 120,
            'BLUE': 240
        }
        base_time = wait_times.get(obj.priority, 120)

        # Ajusta baseado na fila
        queue_size = Triage.objects.filter(
            upa=obj.upa,
            status='TRIAGED',
            priority=obj.priority,
            created_at__lt=obj.created_at
        ).count()

        return base_time + (queue_size * 15)

    def get_position_in_queue(self, obj):
        if obj.status != 'TRIAGED':
            return None

        return Triage.objects.filter(
            upa=obj.upa,
            status='TRIAGED',
            priority=obj.priority,
            created_at__lt=obj.created_at
        ).count() + 1