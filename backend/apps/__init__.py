# apps/__init__.py
# (arquivo vazio)

# apps/core/__init__.py
default_app_config = 'apps.core.apps.CoreConfig'

# apps/core/apps.py
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core'

# apps/facilities/__init__.py
default_app_config = 'apps.facilities.apps.FacilitiesConfig'

# apps/facilities/apps.py
from django.apps import AppConfig

class FacilitiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.facilities'
    verbose_name = 'Facilities'

# apps/triage/__init__.py
default_app_config = 'apps.triage.apps.TriageConfig'

# apps/triage/apps.py
from django.apps import AppConfig

class TriageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.triage'
    verbose_name = 'Triage'

# apps/analytics/__init__.py
default_app_config = 'apps.analytics.apps.AnalyticsConfig'

# apps/analytics/apps.py
from django.apps import AppConfig

class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.analytics'
    verbose_name = 'Analytics'

# apps/analytics/models.py
# Arquivo vazio por enquanto, analytics usa models dos outros apps

# apps/core/management/__init__.py
# (arquivo vazio)

# apps/core/management/commands/__init__.py
# (arquivo vazio)