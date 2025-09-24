from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('OndeAtende', {'fields': ('role', 'professional_id')}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'model_name']
    list_filter = ['action', 'timestamp']
    readonly_fields = ['id', 'timestamp', 'user', 'action', 'model_name', 'object_id', 'details']

    def has_add_permission(self, request):
        return False  # Logs são criados automaticamente

    def has_delete_permission(self, request, obj=None):
        return False  # Logs são imutáveis