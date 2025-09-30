#backend/config/settings.py
"""
Configurações do Django para OndeAtende
Exige todas as variáveis de ambiente sem defaults
"""

import os
import sys
from pathlib import Path
from decouple import config, UndefinedValueError


# Validação rigorosa de ambiente
def validate_required_env():
    """Falha imediatamente se alguma variável obrigatória estiver faltando"""
    required = {
        'SECRET_KEY': 'Chave secreta do Django',
        'DEBUG': 'Modo debug (True/False)',
        'ALLOWED_HOSTS': 'Hosts permitidos (separados por vírgula)',
        'DB_NAME': 'Nome do banco de dados PostgreSQL',
        'DB_USER': 'Usuário do PostgreSQL',
        'DB_PASSWORD': 'Senha do PostgreSQL',
        'DB_HOST': 'Host do PostgreSQL',
        'DB_PORT': 'Porta do PostgreSQL',
        'REDIS_HOST': 'Host do Redis',
        'REDIS_PORT': 'Porta do Redis'
    }

    missing = []
    for var, description in required.items():
        try:
            config(var)
        except UndefinedValueError:
            missing.append(f"  ❌ {var}: {description}")

    if missing:
        print("\n" + "=" * 60)
        print("ERRO: Variáveis de ambiente obrigatórias não encontradas!")
        print("=" * 60)
        print("\nAdicione ao arquivo .env:")
        print("\n".join(missing))
        print("=" * 60 + "\n")
        sys.exit(1)


# Executa validação ANTES de qualquer outra coisa
validate_required_env()

# Base
BASE_DIR = Path(__file__).resolve().parent.parent

# Security - SEM DEFAULTS!
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', cast=bool)
ALLOWED_HOSTS = [h.strip() for h in config('ALLOWED_HOSTS').split(',')]

AUTH_USER_MODEL = 'core.User'

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_spectacular',

    # Apps do projeto
    'apps.core',
    'apps.facilities',
    'apps.triage',
    'apps.analytics',
    'apps.prefecture',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database - EXIGE variáveis!
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', cast=int),
        'CONN_MAX_AGE': 0,
    }
}

# Cache básico
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Passwords
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
}

# CORS
CORS_ALLOW_ALL_ORIGINS = DEBUG
if not DEBUG:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

# i18n
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging básico
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

print(f"✓ Settings carregado: DEBUG={DEBUG}, DB={config('DB_NAME')}@{config('DB_HOST')}")