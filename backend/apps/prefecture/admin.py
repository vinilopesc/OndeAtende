# Arquivo: apps/prefecture/admin.py
# Criar arquivo completo:
from django.contrib import admin
from .models import Prefecture, PrefectureStaff, HealthUnit, Doctor

@admin.register(Prefecture)
class PrefectureAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'state', 'cnpj', 'is_active']
    list_filter = ['state', 'is_active']
    search_fields = ['name', 'city', 'cnpj']

@admin.register(PrefectureStaff)
class PrefectureStaffAdmin(admin.ModelAdmin):
    list_display = ['user', 'prefecture', 'role', 'department']
    list_filter = ['role', 'prefecture']
    search_fields = ['user__username', 'user__email', 'department']

@admin.register(HealthUnit)
class HealthUnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit_type', 'prefecture', 'cnes', 'is_active']
    list_filter = ['unit_type', 'is_active', 'prefecture']
    search_fields = ['name', 'cnes']

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['name', 'crm', 'prefecture', 'is_active']
    list_filter = ['is_active', 'prefecture']
    search_fields = ['name', 'crm', 'cpf']