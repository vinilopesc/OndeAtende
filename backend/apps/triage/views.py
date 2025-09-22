# Arquivo: apps/triage/views.py


@action(detail=True, methods=['post'])
def get_routing(self, request, pk=None):
    """
    Obtém roteamento otimizado pós-triagem
    Body: {lat: float, lng: float}
    """
    session = self.get_object()

    lat = request.data.get('lat')
    lng = request.data.get('lng')

    if not lat or not lng:
        return Response(
            {'error': 'Coordenadas (lat, lng) são obrigatórias'},
            status=status.HTTP_400_BAD_REQUEST
        )

    from apps.triage.routing import TriageRouter
    router = TriageRouter()

    facilities = router.route_patient(
        session,
        float(lat),
        float(lng),
        max_results=3
    )

    # Salva recomendação no banco
    session.triage_notes += f"\n\nUnidades recomendadas: {[f['facility']['name'] for f in facilities]}"
    session.save()

    return Response({
        'session_id': str(session.id),
        'priority': session.priority_color,
        'priority_reason': session.priority_reason,
        'recommended_facilities': facilities,
        'emergency_message': self._get_emergency_message(session.priority_color)
    })


def _get_emergency_message(self, priority: str) -> Optional[str]:
    """Mensagem de emergência baseada na prioridade"""
    if priority == 'RED':
        return "EMERGÊNCIA MÉDICA! Ligue 192 IMEDIATAMENTE ou vá ao hospital mais próximo!"
    elif priority == 'ORANGE':
        return "Situação muito urgente. Procure atendimento em até 10 minutos."
    return None