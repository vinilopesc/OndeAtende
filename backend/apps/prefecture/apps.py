# Arquivo: apps/prefecture/apps.py

from django.apps import AppConfig


class PrefectureConfig(AppConfig):
    """
    Configuração da aplicação Prefecture.
    Este arquivo deve conter apenas configurações básicas,
    sem imports de bibliotecas que dependem do Django.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.prefecture'
    verbose_name = 'Prefeitura'