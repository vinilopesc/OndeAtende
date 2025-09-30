# Arquivo: apps/prefecture/admin.py
# Substituir todo o conteúdo por:
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.core.models import User
from .models import Prefecture, PrefectureStaff, HealthUnit, Doctor


# Inline para mostrar o perfil de prefeitura dentro do usuário
class PrefectureStaffInline(admin.StackedInline):
    model = PrefectureStaff
    can_delete = False
    verbose_name = 'Perfil de Prefeitura'
    verbose_name_plural = 'Perfil de Prefeitura'
    fk_name = 'user'


# Extender o admin do User para incluir o perfil de prefeitura
class UserAdmin(BaseUserAdmin):
    inlines = [PrefectureStaffInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_prefecture_staff']

    def is_prefecture_staff(self, obj):
        return hasattr(obj, 'prefecture_profile')

    is_prefecture_staff.boolean = True
    is_prefecture_staff.short_description = 'Staff Prefeitura'


# Re-registrar o User com o novo admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Prefecture)
class PrefectureAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'state', 'cnpj', 'is_active', 'created_at']
    list_filter = ['state', 'is_active', 'created_at']
    search_fields = ['name', 'city', 'cnpj']
    date_hierarchy = 'created_at'


@admin.register(PrefectureStaff)
class PrefectureStaffAdmin(admin.ModelAdmin):
    list_display = ['user', 'prefecture', 'role', 'department', 'phone']
    list_filter = ['role', 'prefecture']
    search_fields = ['user__username', 'user__email', 'department']
    raw_id_fields = ['user']  # Para facilitar a busca quando tiver muitos usuários


@admin.register(HealthUnit)
class HealthUnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit_type', 'prefecture', 'cnes', 'is_active', 'created_at']
    list_filter = ['unit_type', 'is_active', 'prefecture', 'created_at']
    search_fields = ['name', 'cnes', 'address']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'unit_type', 'prefecture')
        }),
        ('Identificação', {
            'fields': ('cnes',)
        }),
        ('Contato', {
            'fields': ('address', 'phone')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['name', 'crm', 'prefecture', 'has_user_account', 'is_active']
    list_filter = ['is_active', 'prefecture']
    search_fields = ['name', 'crm', 'cpf', 'email']
    filter_horizontal = []  # Se tivéssemos relações many-to-many

    def has_user_account(self, obj):
        return obj.user is not None

    has_user_account.boolean = True
    has_user_account.short_description = 'Tem Acesso ao Sistema'

    fieldsets = (
        ('Identificação', {
            'fields': ('name', 'crm', 'cpf')
        }),
        ('Informações Profissionais', {
            'fields': ('specialties', 'prefecture')
        }),
        ('Contato', {
            'fields': ('email', 'phone')
        }),
        ('Sistema', {
            'fields': ('user', 'is_active'),
            'description': 'Configurações de acesso ao sistema'
        })
    )


# Personalizar o header do admin
admin.site.site_header = 'OndeAtende - Administração'
admin.site.site_title = 'OndeAtende Admin'
admin.site.index_title = 'Painel de Administração'