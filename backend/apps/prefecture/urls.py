# Arquivo: apps/prefecture/urls.py
# Criar arquivo completo:
from django.urls import path, include
from .views import test_login_page
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import AuthViewSet, HealthUnitViewSet, DoctorViewSet, MetricsViewSet

# Configura o roteador do Django REST Framework
router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'health-units', HealthUnitViewSet, basename='health-unit')
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'metrics', MetricsViewSet, basename='metrics')

urlpatterns = [
    path('', include(router.urls)),
    path('test-login/', test_login_page, name='test-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
