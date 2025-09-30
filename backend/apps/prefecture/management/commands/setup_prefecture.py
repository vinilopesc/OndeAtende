# Arquivo: apps/prefecture/management/commands/setup_prefecture.py
# Criar a estrutura de diretórios primeiro:
# mkdir -p apps/prefecture/management/commands
# touch apps/prefecture/management/__init__.py
# touch apps/prefecture/management/commands/__init__.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.prefecture.models import Prefecture, PrefectureStaff
from apps.core.models import User


class Command(BaseCommand):
    help = 'Configura dados iniciais da prefeitura'

    def handle(self, *args, **options):
        # Criar prefeitura se não existir
        prefecture, created = Prefecture.objects.get_or_create(
            cnpj='18.251.936/0001-54',
            defaults={
                'name': 'Prefeitura de Montes Claros',
                'city': 'Montes Claros',
                'state': 'MG'
            }
        )

        if created:
            self.stdout.write(f'✅ Prefeitura criada: {prefecture.name}')

        # Criar usuário administrador da prefeitura
        username = 'admin.prefeitura'
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                email='admin@montesclaros.mg.gov.br',
                password='Moc@2024!',
                first_name='Administrador',
                last_name='Sistema',
                role='ADMIN'  # Role médico como ADMIN
            )

            # Criar perfil de prefeitura
            PrefectureStaff.objects.create(
                user=user,
                prefecture=prefecture,
                role='admin',  # Role administrativo também como admin
                department='Secretaria de Saúde'
            )

            self.stdout.write(f'✅ Usuário admin criado: {username} / Moc@2024!')
        else:
            self.stdout.write('⚠️ Usuário admin já existe')

        # Mostrar resumo
        self.stdout.write('\n📊 Resumo do Sistema:')
        self.stdout.write(f'   Prefeitura: {prefecture.name}')
        self.stdout.write(f'   Staff da prefeitura: {PrefectureStaff.objects.count()} funcionário(s)')
        self.stdout.write(f'   Total de usuários: {User.objects.count()}')