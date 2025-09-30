"""
URLs principais do OndeAtende - MVP simplificado
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.shortcuts import redirect


def index_view(request):
    """
    View da página inicial - redireciona para admin
    Em produção, isso seria a landing page ou redirecionaria para o frontend
    """
    return redirect('/admin/')


def healthcheck(request):
    """Health check endpoint para monitoramento"""
    return JsonResponse({
        "status": "healthy",
        "service": "OndeAtende Backend",
        "version": "1.0.0-mvp"
    })


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Página inicial
    path('', index_view, name='index'),

    path('api/prefecture/', include('apps.prefecture.urls')),

    # Health check
    path('health/', healthcheck, name='healthcheck'),
    path('healthz/', healthcheck)

]

# Customização do admin
admin.site.site_header = "OndeAtende Admin"
admin.site.site_title = "OndeAtende"
admin.site.index_title = "Painel de Controle"