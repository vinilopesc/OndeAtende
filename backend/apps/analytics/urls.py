# apps/analytics/urls.py
from django.urls import path
from .views import DashboardView, ReportsView

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='analytics-dashboard'),
    path('reports/', ReportsView.as_view(), name='analytics-reports'),
]