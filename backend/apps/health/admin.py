from django.contrib import admin
from .models import Symptom, MedicalShift, Triage

@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_priority', 'description']
    list_filter = ['base_priority']
    search_fields = ['name', 'keywords']

@admin.register(MedicalShift)
class MedicalShiftAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'upa', 'specialty', 'start_time', 'end_time', 'is_active']
    list_filter = ['upa', 'specialty', 'is_active']
    search_fields = ['doctor__first_name', 'doctor__last_name', 'specialty']
    date_hierarchy = 'start_time'

@admin.register(Triage)
class TriageAdmin(admin.ModelAdmin):
    list_display = ['patient_name', 'upa', 'priority', 'status', 'created_at']
    list_filter = ['priority', 'status', 'upa']
    search_fields = ['patient_name', 'patient_cpf']
    readonly_fields = ['priority', 'priority_reason', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'