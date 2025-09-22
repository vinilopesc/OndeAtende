# Arquivo: apps/facilities/views.py


from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, F
from .models import MedicalShift, MedicalSpecialty
from .serializers import FacilityWithShiftsSerializer, MedicalSpecialtySerializer


class FacilitySearchViewSet(viewsets.ReadOnlyModelViewSet):
    """Busca inteligente de unidades com especialidades"""
    queryset = Facility.objects.all()
    serializer_class = FacilityWithShiftsSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def search_by_specialty(self, request):
        """
        Busca unidades com especialidade específica em plantão
        Query params:
        - specialty: código da especialidade (obrigatório)
        - lat/lng: coordenadas do usuário
        - urgency: nível de urgência (RED/ORANGE/YELLOW/GREEN/BLUE)
        - date: data do plantão (default: hoje)
        """
        specialty_code = request.query_params.get('specialty')
        if not specialty_code:
            return Response(
                {'error': 'Parâmetro specialty é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Data do plantão
        from django.utils import timezone
        date_str = request.query_params.get('date')
        if date_str:
            from datetime import datetime
            search_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            search_date = timezone.localdate()

        # Busca unidades com a especialidade
        facilities = Facility.objects.filter(
            shifts__specialty__code=specialty_code,
            shifts__shift_date=search_date,
            shifts__status__in=['SCHEDULED', 'ACTIVE']
        ).distinct()

        # Filtra por urgência
        urgency = request.query_params.get('urgency')
        if urgency in ['RED', 'ORANGE']:
            # Apenas emergências
            facilities = facilities.filter(
                facility_type__in=['HOSPITAL', 'PS', 'UPA'],
                is_accepting_emergencies=True
            )
        elif urgency in ['YELLOW']:
            # UPAs e hospitais
            facilities = facilities.filter(
                facility_type__in=['UPA', 'HOSPITAL', 'PS']
            )

        # Calcula score baseado em distância e ocupação
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')

        results = []
        for facility in facilities:
            score = 100  # Base score

            # Penaliza por ocupação
            score -= facility.current_occupancy_percent * 0.5

            # Calcula distância se coordenadas fornecidas
            distance = None
            if lat and lng:
                try:
                    distance = facility.calculate_distance_from(float(lat), float(lng))
                    score -= distance * 2  # Penaliza 2 pontos por km
                except:
                    pass

            # Bonus por tipo de unidade baseado na urgência
            if urgency in ['RED', 'ORANGE'] and facility.facility_type == 'HOSPITAL':
                score += 20
            elif urgency in ['YELLOW', 'GREEN'] and facility.facility_type == 'UPA':
                score += 10

            results.append({
                'facility': FacilityWithShiftsSerializer(facility, context={'request': request}).data,
                'score': max(0, score),
                'distance_km': distance,
                'estimated_wait_minutes': facility.average_wait_time_minutes
            })

        # Ordena por score
        results.sort(key=lambda x: x['score'], reverse=True)

        return Response({
            'specialty': specialty_code,
            'date': search_date.isoformat(),
            'total_results': len(results),
            'results': results[:10]  # Top 10
        })

    @action(detail=False, methods=['get'])
    def available_specialties(self, request):
        """Lista todas especialidades disponíveis hoje"""
        from django.utils import timezone
        today = timezone.localdate()

        specialties = MedicalSpecialty.objects.filter(
            medicalshift__shift_date=today,
            medicalshift__status__in=['SCHEDULED', 'ACTIVE']
        ).annotate(
            facility_count=Count('medicalshift__facility', distinct=True)
        ).distinct()

        return Response(
            MedicalSpecialtySerializer(specialties, many=True).data
        )