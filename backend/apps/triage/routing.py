# apps/triage/routing.py
"""
Configuração de roteamento WebSocket para sistema de triagem
"""

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('', consumers.TriageQueueConsumer.as_asgi()),
    path('waiting/', consumers.PatientQueueConsumer.as_asgi()),
]