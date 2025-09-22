# apps/core/urls.py
from django.urls import path
from .views import (
    CustomAuthToken,
    logout_view,
    current_user,
    change_password
)

urlpatterns = [
    path('login/', CustomAuthToken.as_view(), name='auth-login'),
    path('logout/', logout_view, name='auth-logout'),
    path('me/', current_user, name='auth-current-user'),
    path('change-password/', change_password, name='auth-change-password'),
]