# backend/config/settings/base.py
"""
Configurações base do Django para OndeAtende
Sistema de Triagem Médica com Protocolo Manchester
"""

import os
from pathlib import Path
from decouple import config, Csv
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from datetime import timedelta

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent

# Segurança
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())

# Aplicações
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',  # Para campos especiais PostgreSQL
    'django.contrib.gis',  # Para geolocalização
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',
    'channels',
    'drf_spectacular',  # OpenAPI/Swagger
    'django_prometheus',  # Métricas
    'storages',  # S3/MinIO
    'django_extensions',
    'simple_history',  # Auditoria
    'django_cryptography',  # Criptografia de campos
]

LOCAL_APPS = [
    'apps.core',
    'apps.facilities',
    'apps.triage',
    'apps.analytics',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Middleware
MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',  # Métricas
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',  # Auditoria
    'apps.core.middleware.HIPAASecurityMiddleware',  # HIPAA compliance
    'apps.core.middleware.AuditLoggingMiddleware',  # Log de auditoria
    'django_prometheus.middleware.PrometheusAfterMiddleware',  # Métricas
]

ROOT_URLCONF = 'config.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

# WSGI/ASGI
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database com Read Replica
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': config('DB_NAME', default='ondeatende'),
        'USER': config('DB_USER', default='ondeatende_user'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432', cast=int),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
            'sslmode': 'require' if not DEBUG else 'prefer',
        },
    },
    'replica': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': config('DB_NAME', default='ondeatende'),
        'USER': config('DB_USER', default='ondeatende_user'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_REPLICA_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432', cast=int),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
            'sslmode': 'require' if not DEBUG else 'prefer',
        },
    }
}

# Database Router para Read/Write splitting
DATABASE_ROUTERS = ['apps.core.routers.PrimaryReplicaRouter']

# Redis Cache e Session
REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default=6379, cast=int)
REDIS_PASSWORD = config('REDIS_PASSWORD', default='')
REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'{REDIS_URL}/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': 'ondeatende',
        'TIMEOUT': 300,  # 5 minutos padrão
    },
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'{REDIS_URL}/2',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    },
    'websocket': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'{REDIS_URL}/3',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    },
}

# Session usando Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'
SESSION_COOKIE_AGE = 900  # 15 minutos para workstations médicas
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Channels (WebSockets)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(REDIS_HOST, REDIS_PORT)],
            'capacity': 10000,
            'expiry': 60,
        },
    },
}

# Celery Configuration
CELERY_BROKER_URL = f'amqp://{config("RABBITMQ_USER", default="guest")}:{config("RABBITMQ_PASSWORD", default="guest")}@{config("RABBITMQ_HOST", default="localhost")}:5672/{config("RABBITMQ_VHOST", default="/")}'
CELERY_RESULT_BACKEND = f'{REDIS_URL}/4'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Sao_Paulo'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutos

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'clean-old-sessions': {
        'task': 'apps.triage.tasks.clean_old_sessions',
        'schedule': timedelta(hours=1),
    },
    'calculate-analytics': {
        'task': 'apps.analytics.tasks.calculate_daily_metrics',
        'schedule': timedelta(hours=24),
    },
    'check-facility-status': {
        'task': 'apps.facilities.tasks.update_facility_status',
        'schedule': timedelta(minutes=5),
    },
    'backup-database': {
        'task': 'apps.core.tasks.backup_database',
        'schedule': timedelta(hours=6),
    },
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {'NAME': 'apps.core.validators.MedicalPasswordValidator'},  # Validador customizado
]

# Autenticação
AUTH_USER_MODEL = 'core.User'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'apps.core.backends.LDAPBackend',  # Para integração com AD hospitalar
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S%z',
    'DATE_FORMAT': '%Y-%m-%d',
    'TIME_FORMAT': '%H:%M:%S',
}

# CORS
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='', cast=Csv())
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Security Headers
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# AWS S3 / MinIO (produção)
if not DEBUG:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL', default=None)
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = 'private'
    AWS_S3_ENCRYPTION = True
    AWS_S3_SIGNATURE_VERSION = 's3v4'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'ondeatende.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'audit': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'audit.log',
            'maxBytes': 1024 * 1024 * 50,  # 50 MB
            'backupCount': 30,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'audit': {
            'handlers': ['audit'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Sentry Error Tracking
if not DEBUG:
    sentry_sdk.init(
        dsn=config('SENTRY_DSN', default=''),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,  # HIPAA compliance
        environment=config('ENVIRONMENT', default='production'),
    )

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True
USE_TZ = True
LANGUAGES = [
    ('pt-br', 'Português'),
    ('en', 'English'),
    ('es', 'Español'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@ondeatende.com')

# Criptografia PHI (Protected Health Information)
ENCRYPTION_KEY = config('ENCRYPTION_KEY')  # 32-byte key base64 encoded

# Manchester Triage System
MANCHESTER_VERSION = '3.0'
MANCHESTER_TIMEOUT_MINUTES = 5  # Tempo máximo para completar triagem

# Sistema de Saúde
HEALTH_SYSTEM_CODE = 'SUS'  # Sistema Único de Saúde
CNES_API_URL = 'http://cnes.datasus.gov.br/api/'  # API do CNES

# OpenAPI/Swagger
SPECTACULAR_SETTINGS = {
    'TITLE': 'OndeAtende API',
    'DESCRIPTION': 'Sistema de Triagem Médica com Protocolo Manchester',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': r'/api/v[0-9]',
    'COMPONENT_SPLIT_REQUEST': True,
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

---
# backend/requirements/base.txt
# Requirements base para OndeAtende

# Django Core
Django==5.0.1
django-environ==0.11.2
python-decouple==3.8

# PostgreSQL
psycopg2-binary==2.9.9
dj-database-url==2.1.0

# REST API
djangorestframework==3.14.0
django-cors-headers==4.3.1
django-filter==23.5
drf-spectacular==0.27.0
djangorestframework-simplejwt==5.3.1

# Redis & Cache
redis==5.0.1
hiredis==2.3.2
django-redis==5.4.0

# Celery
celery==5.3.4
django-celery-beat==2.5.0
django-celery-results==2.5.1
kombu==5.3.4
amqp==5.2.0

# WebSockets
channels==4.0.0
channels-redis==4.1.0
daphne==4.0.0

# Security & Cryptography
cryptography==41.0.7
django-cryptography==1.1
pycryptodome==3.19.0
PyJWT==2.8.0

# Monitoring
sentry-sdk==1.39.1
django-prometheus==2.3.1

# Storage
boto3==1.34.11
django-storages==1.14.2
Pillow==10.1.0

# Utilities
python-dateutil==2.8.2
pytz==2023.3
requests==2.31.0
httpx==0.25.2

# Data Processing
pandas==2.1.4
numpy==1.26.2

# Audit & History
django-simple-history==3.4.0

# Admin Enhancement
django-extensions==3.2.3

# Testing (moved to dev in production)
pytest==7.4.3
pytest-django==4.7.0
factory-boy==3.3.0
faker==20.1.0

---
# backend/requirements/production.txt
-r base.txt

# Production servers
gunicorn==21.2.0
uvicorn[standard]==0.25.0
whitenoise==6.6.0

# Production database
pgbouncer==0.0.9
django-postgrespool2==2.0.1

# Production monitoring
elastic-apm==6.19.0
python-json-logger==2.0.7

# Security scanning
safety==3.0.1
bandit==1.7.5

# Performance
django-cachalot==2.6.1
django-silk==5.0.4

---
# .github/workflows/ci-cd.yml
# CI/CD Pipeline para OndeAtende

name: OndeAtende CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '20'

jobs:
  # Job: Testes e Qualidade de Código
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements/*.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/requirements/base.txt
        pip install -r backend/requirements/test.txt
    
    - name: Run security checks
      run: |
        bandit -r backend/apps/ -f json -o bandit-report.json
        safety check --json > safety-report.json
    
    - name: Run linting
      run: |
        cd backend
        flake8 apps/ --config=.flake8
        black --check apps/
        isort --check-only apps/
    
    - name: Run tests with coverage
      env:
        DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_ondeatende
        REDIS_URL: redis://localhost:6379/0
        SECRET_KEY: test-secret-key
        ENCRYPTION_KEY: "test-encryption-key-32-bytes-long!!"
      run: |
        cd backend
        pytest --cov=apps --cov-report=xml --cov-report=html
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
    
    - name: SonarCloud Scan
      uses: SonarSource/sonarcloud-github-action@master
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
  
  # Job: Build Docker Images
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Docker Hub
      uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push Backend
      uses: docker/build-push-action@v5
      with:
        context: ./backend
        push: true
        tags: |
          ondeatende/backend:latest
          ondeatende/backend:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
    
    - name: Build and push Frontend
      uses: docker/build-push-action@v5
      with:
        context: ./frontend
        push: true
        tags: |
          ondeatende/frontend:latest
          ondeatende/frontend:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
  
  # Job: Deploy to Kubernetes
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
      with:
        version: 'latest'
    
    - name: Configure kubectl
      run: |
        echo "${{ secrets.KUBE_CONFIG }}" | base64 --decode > kubeconfig
        export KUBECONFIG=kubeconfig
    
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/ondeatende-backend backend=ondeatende/backend:${{ github.sha }} -n ondeatende
        kubectl set image deployment/ondeatende-frontend frontend=ondeatende/frontend:${{ github.sha }} -n ondeatende
        kubectl rollout status deployment/ondeatende-backend -n ondeatende
        kubectl rollout status deployment/ondeatende-frontend -n ondeatende
    
    - name: Run smoke tests
      run: |
        ./scripts/smoke-tests.sh ${{ secrets.PRODUCTION_URL }}