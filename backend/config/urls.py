# config/urls.py
"""
URLs principais do OndeAtende
Organiza rotas por domínio com versionamento de API
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)
from apps.core.views import healthz

# API v1 patterns
api_v1_patterns = [
    path('facilities/', include('apps.facilities.urls')),
    path('triage/', include('apps.triage.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('auth/', include('apps.core.urls')),
]

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check
    path('healthz/', healthz, name='healthz'),
    
    # API v1
    path('api/v1/', include(api_v1_patterns)),
    
    # OpenAPI/Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Prometheus metrics
    path('metrics/', include('django_prometheus.urls')),
]

# WebSocket routing
websocket_urlpatterns = [
    path('ws/triage/<str:facility_id>/', include('apps.triage.routing.websocket_urlpatterns')),
]

# Static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Configure admin site
admin.site.site_header = "OndeAtende Admin"
admin.site.site_title = "OndeAtende"
admin.site.index_title = "Sistema de Triagem Manchester"