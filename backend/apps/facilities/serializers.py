# Arquivo: apps/facilities/serializers.py

from .models import MedicalShift, MedicalSpecialty


class MedicalSpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalSpecialty
        fields = ['id', 'code', 'name', 'description', 'requires_emergency']


class MedicalShiftSerializer(serializers.ModelSerializer):
    specialty_name = serializers.CharField(source='specialty.name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = MedicalShift
        fields = [
            'id', 'specialty', 'specialty_name', 'doctor_name',
            'shift_date', 'start_time', 'end_time', 'is_on_call',
            'max_appointments', 'current_appointments', 'status',
            'is_available'
        ]

    def get_is_available(self, obj):
        return obj.is_available_now()


class FacilityWithShiftsSerializer(FacilitySerializer):
    """Serializer estendido com plantões ativos"""
    active_shifts = serializers.SerializerMethodField()
    available_specialties = serializers.SerializerMethodField()

    class Meta(FacilitySerializer.Meta):
        fields = FacilitySerializer.Meta.fields + ['active_shifts', 'available_specialties']

    def get_active_shifts(self, obj):
        """Retorna plantões ativos hoje"""
        from django.utils import timezone
        today = timezone.localdate()

        shifts = MedicalShift.objects.filter(
            facility=obj,
            shift_date=today,
            status__in=['SCHEDULED', 'ACTIVE']
        ).select_related('specialty', 'doctor')

        return MedicalShiftSerializer(shifts, many=True).data

    def get_available_specialties(self, obj):
        """Lista especialidades disponíveis agora"""
        from django.utils import timezone
        now = timezone.localtime()

        specialties = MedicalSpecialty.objects.filter(
            medicalshift__facility=obj,
            medicalshift__shift_date=now.date(),
            medicalshift__status='ACTIVE'
        ).distinct()

        return [s.code for s in specialties]