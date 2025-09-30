# Arquivo: apps/prefecture/models.py
# Substituir todo o arquivo por esta versão completa e comentada:

from django.db import models
from django.conf import settings
from django.utils import timezone


class Prefecture(models.Model):
    """
    Representa uma prefeitura no sistema.

    A prefeitura é a entidade administrativa que gerencia hospitais,
    UPAs, postos de saúde e as escalas dos profissionais de saúde.
    É como a "central de comando" do sistema de saúde municipal.
    """
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
    Perfil administrativo para funcionários da prefeitura.

    IMPORTANTE: Este modelo é diferente do staff médico (core.User).
    - core.User: Define profissionais de saúde (médicos, enfermeiros)
    - PrefectureStaff: Define gestores municipais que administram o sistema

    Um usuário pode ser apenas staff da prefeitura (gestor), apenas
    staff médico (profissional de saúde), ou ambos (médico que também
    tem cargo administrativo na prefeitura).
    """
    ROLE_CHOICES = [
        ('admin', 'Administrador'),  # Acesso total ao sistema
        ('operator', 'Operador'),  # Pode criar/editar recursos
        ('viewer', 'Visualizador')  # Apenas visualização
    ]

    # Relacionamento com o modelo User do core
    # Um usuário do sistema pode ter um perfil de prefeitura
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Aponta para core.User
        on_delete=models.CASCADE,
        related_name='prefecture_profile',
        verbose_name='Usuário',
        help_text='Usuário do sistema vinculado a este perfil administrativo'
    )

    # Cada funcionário pertence a uma prefeitura
    prefecture = models.ForeignKey(
        Prefecture,
        on_delete=models.CASCADE,
        related_name='staff_members',
        verbose_name='Prefeitura'
    )

    # Papel administrativo (diferente do papel médico em core.User)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='viewer',
        verbose_name='Papel Administrativo',
        help_text='Define as permissões administrativas no sistema da prefeitura'
    )

    # Informações adicionais do funcionário
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Departamento',
        help_text='Ex: Secretaria de Saúde, Coordenação de UPAs, etc.'
    )

    class Meta:
        db_table = 'prefecture_staff'
        verbose_name = 'Funcionário da Prefeitura'
        verbose_name_plural = 'Funcionários da Prefeitura'
        indexes = [
            models.Index(fields=['prefecture', 'user']),
            models.Index(fields=['role'])
        ]
        unique_together = [['user', 'prefecture']]

    def __str__(self):
        # Como core.User herda de AbstractUser, temos acesso a first_name e last_name
        user_name = self.user.get_full_name() or self.user.username
        return f"{user_name} - {self.prefecture.name} ({self.get_role_display()})"

    @property
    def is_admin(self):
        """Verifica se é administrador da prefeitura"""
        return self.role == 'admin'

    @property
    def can_edit(self):
        """Verifica se pode editar recursos (admin ou operator)"""
        return self.role in ['admin', 'operator']

    @property
    def medical_role(self):
        """
        Retorna o papel médico do usuário, se houver.
        Útil para casos onde um médico também é gestor.
        """
        if hasattr(self.user, 'role'):
            return self.user.get_role_display()
        return None


class HealthUnit(models.Model):
    """
    Unidades de saúde gerenciadas pela prefeitura.

    Estas são as unidades físicas onde o staff médico (core.User)
    trabalha. A prefeitura gerencia estas unidades, define escalas
    e aloca profissionais.
    """
    UNIT_TYPES = [
        ('upa', 'UPA'),  # Unidade de Pronto Atendimento
        ('hospital', 'Hospital'),  # Hospital completo
        ('posto', 'Posto de Saúde'),  # Atenção básica
        ('especializado', 'Centro Especializado')  # Ex: CAPS, CER, etc.
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
    """
    Registro de médicos para gestão administrativa pela prefeitura.

    NOTA: Este modelo é para GESTÃO ADMINISTRATIVA de médicos.
    O modelo core.User (com role='DOCTOR') é para AUTENTICAÇÃO
    e OPERAÇÃO do sistema pelos médicos.

    Um médico pode:
    1. Estar apenas cadastrado aqui (para escalas/gestão)
    2. Ter também um usuário no sistema (core.User com role='DOCTOR')
    3. Ter também perfil administrativo (PrefectureStaff)
    """
    prefecture = models.ForeignKey(
        Prefecture,
        on_delete=models.CASCADE,
        related_name='doctors',
        verbose_name='Prefeitura'
    )

    # Vínculo opcional com usuário do sistema
    # Nem todo médico cadastrado precisa ter acesso ao sistema
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doctor_profile',
        verbose_name='Usuário no Sistema',
        help_text='Conta de usuário para médicos que acessam o sistema'
    )

    # Informações do médico para gestão
    name = models.CharField(max_length=200, verbose_name='Nome Completo')
    crm = models.CharField(max_length=20, verbose_name='CRM')
    cpf = models.CharField(max_length=14, unique=True, verbose_name='CPF')
    specialties = models.JSONField(
        default=list,
        verbose_name='Especialidades',
        help_text='Lista de especialidades. Ex: ["Clínica Geral", "Pediatria"]'
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

    @property
    def has_system_access(self):
        """Verifica se o médico tem acesso ao sistema"""
        return self.user is not None

    def create_user_account(self, password=None):
        """
        Cria uma conta de usuário para este médico acessar o sistema.
        Útil quando um médico cadastrado precisa começar a usar o sistema.
        """
        if self.user:
            return self.user

        from apps.core.models import User

        # Cria username baseado no CRM
        username = f"dr_{self.crm.lower().replace('/', '_')}"

        user = User.objects.create_user(
            username=username,
            email=self.email,
            password=password or User.objects.make_random_password(),
            first_name=self.name.split()[0],
            last_name=' '.join(self.name.split()[1:]),
            role='DOCTOR'  # Define como médico no sistema
        )

        self.user = user
        self.save()
        return user