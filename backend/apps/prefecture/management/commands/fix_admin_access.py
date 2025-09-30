# Arquivo: apps/prefecture/management/commands/fix_admin_access.py
# Criar este novo comando
from django.core.management.base import BaseCommand
from apps.core.models import User


class Command(BaseCommand):
    help = 'Corrige acesso ao admin para usuário da prefeitura'

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username='admin.prefeitura')

            # Dar permissões de staff e superuser
            user.is_staff = True  # Permite acesso ao Django Admin
            user.is_superuser = True  # Dá todas as permissões
            user.save()

            self.stdout.write(self.style.SUCCESS(
                f'✅ Usuário {user.username} agora tem acesso completo ao admin!'
            ))
            self.stdout.write(
                f'📌 Acesse: http://localhost:8000/admin\n'
                f'   Usuário: admin.prefeitura\n'
                f'   Senha: Moc@2024!'
            )

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                '❌ Usuário admin.prefeitura não encontrado! Execute primeiro: python manage.py setup_prefecture'
            ))