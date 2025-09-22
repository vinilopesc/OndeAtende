# apps/triage/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TriageSessionViewSet, PatientViewSet, PublicTriageViewSet, FacilityViewSet

router = DefaultRouter()
router.register(r'sessions', TriageSessionViewSet, basename='triage-session')
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'facilities', FacilityViewSet, basename='facility')
router.register(r'public', PublicTriageViewSet, basename='public-triage')

urlpatterns = router.urls