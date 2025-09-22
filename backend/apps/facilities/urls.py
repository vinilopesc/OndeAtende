# apps/facilities/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FacilityViewSet, FacilitySearchViewSet

router = DefaultRouter()
router.register(r'units', FacilityViewSet, basename='facility')
router.register(r'search', FacilitySearchViewSet, basename='facility-search')

urlpatterns = router.urls