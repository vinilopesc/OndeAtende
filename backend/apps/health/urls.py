from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SymptomViewSet, MedicalShiftViewSet, TriageViewSet

router = DefaultRouter()
router.register(r'symptoms', SymptomViewSet, basename='symptom')
router.register(r'shifts', MedicalShiftViewSet, basename='shift')
router.register(r'triages', TriageViewSet, basename='triage')

urlpatterns = [
    path('', include(router.urls)),
]