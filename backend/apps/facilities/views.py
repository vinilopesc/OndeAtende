# apps/facilities/views.py
"""
ViewSets para gerenciamento de unidades de saúde e plantões médicos
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Count, F
from django.utils import timezone
from .models import Facility, MedicalShift, MedicalSpecialty
from .serializers import (
    FacilitySerializer,
    FacilityWithShiftsSerializer,
    MedicalSpecialtySerializer,
    MedicalShiftSerializer
)
import logging

logger = logging.getLogger(__name__)


class FacilityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet público para consulta de unidades de saúde
    """
    queryset = Facility.objects.filter(is_active=True)
    serializer_class = FacilitySerializer
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'with_shifts']:
            return FacilityWithShiftsSerializer
        return FacilitySerializer
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Retorna unidades próximas às coordenadas fornecidas
        Query params: lat, lng, radius (km)
        """
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 10))
        
        if not lat or not lng:
            return Response(
                {'error': 'Latitude e longitude são obrigatórias'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            return Response(
                {'error': 'Coordenadas inválidas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Busca unidades dentro do raio
        facilities = []
        for facility in self.queryset:
            distance = facility.calculate_distance_from(lat, lng)
            if distance <= radius:
                facilities.append({
                    'facility': FacilitySerializer(facility).data,
                    'distance_km': round(distance, 2)
                })
        
        # Ordena por distância
        facilities.sort(key=lambda x: x['distance_km'])
        
        return Response({
            'total': len(facilities),
            'radius_km': radius,
            'results': facilities
        })
    
    @action(detail=True, methods=['get'])
    def current_queue(self, request, pk=None):
        """
        Retorna estado atual da fila da unidade
        """
        facility = self.get_object()
        queue_status = facility.get_current_queue_status()
        
        return Response({
            'facility_id': str(facility.id),
            'facility_name': facility.name,
            'timestamp': timezone.now().isoformat(),
            'queue': queue_status
        })
    
    @action(detail=True, methods=['get'])
    def today_shifts(self, request, pk=None):
        """
        Retorna plantões do dia na unidade
        """
        facility = self.get_object()
        today = timezone.localdate()
        
        shifts = MedicalShift.objects.filter(
            facility=facility,
            shift_date=today
        ).select_related('specialty', 'doctor')
        
        serializer = MedicalShiftSerializer(shifts, many=True)
        return Response(serializer.data)


class FacilitySearchViewSet(viewsets.GenericViewSet):
    """
    ViewSet para busca avançada de unidades
    """
    queryset = Facility.objects.filter(is_active=True)
    serializer_class = FacilityWithShiftsSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def by_specialty(self, request):
        """
        Busca unidades com especialidade específica em plantão
        """
        specialty_code = request.query_params.get('specialty')
        date_str = request.query_params.get('date')
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        urgency = request.query_params.get('urgency')
        
        if not specialty_code:
            return Response(
                {'error': 'Especialidade é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Data do plantão
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
        if urgency in ['RED', 'ORANGE']:
            facilities = facilities.filter(
                facility_type__in=['HOSPITAL', 'PS', 'UPA'],
                is_accepting_emergencies=True
            )
        elif urgency in ['YELLOW']:
            facilities = facilities.filter(
                facility_type__in=['UPA', 'HOSPITAL', 'PS']
            )
        
        # Processa resultados com score
        results = []
        for facility in facilities:
            score = 100
            distance = None
            
            # Calcula distância e ajusta score
            if lat and lng:
                try:
                    distance = facility.calculate_distance_from(float(lat), float(lng))
                    score -= distance * 2
                except:
                    pass
            
            # Ajusta por ocupação
            score -= facility.current_occupancy_percent * 0.5
            
            # Bonus por tipo
            if urgency in ['RED', 'ORANGE'] and facility.facility_type == 'HOSPITAL':
                score += 20
            
            results.append({
                'facility': FacilityWithShiftsSerializer(
                    facility, 
                    context={'request': request}
                ).data,
                'score': max(0, score),
                'distance_km': round(distance, 2) if distance else None,
                'estimated_wait': facility.average_wait_time_minutes,
                'recommended': score > 70
            })
        
        # Ordena por score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return Response({
            'specialty': specialty_code,
            'date': search_date.isoformat(),
            'total': len(results),
            'results': results[:10]
        })
    
    @action(detail=False, methods=['get'])
    def emergency(self, request):
        """
        Retorna unidades de emergência abertas
        """
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        
        # Filtra apenas emergências abertas
        facilities = Facility.objects.filter(
            facility_type__in=['HOSPITAL', 'PS', 'UPA'],
            is_accepting_emergencies=True,
            is_active=True
        )
        
        results = []
        for facility in facilities:
            data = {
                'facility': FacilitySerializer(facility).data,
                'queue_status': facility.get_current_queue_status(),
                'is_open': facility.is_open_now()
            }
            
            # Adiciona distância se coordenadas fornecidas
            if lat and lng:
                try:
                    distance = facility.calculate_distance_from(float(lat), float(lng))
                    data['distance_km'] = round(distance, 2)
                except:
                    pass
            
            results.append(data)
        
        # Ordena por distância se disponível
        if lat and lng:
            results.sort(key=lambda x: x.get('distance_km', 999))
        
        return Response({
            'total': len(results),
            'results': results
        })


class MedicalSpecialtyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para especialidades médicas
    """
    queryset = MedicalSpecialty.objects.all()
    serializer_class = MedicalSpecialtySerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def available_today(self, request):
        """
        Lista especialidades com plantões hoje
        """
        today = timezone.localdate()
        
        specialties = MedicalSpecialty.objects.filter(
            medicalshift__shift_date=today,
            medicalshift__status__in=['SCHEDULED', 'ACTIVE']
        ).annotate(
            facility_count=Count('medicalshift__facility', distinct=True),
            shift_count=Count('medicalshift')
        ).distinct()
        
        results = []
        for specialty in specialties:
            results.append({
                'specialty': MedicalSpecialtySerializer(specialty).data,
                'facilities_available': specialty.facility_count,
                'shifts_today': specialty.shift_count
            })
        
        return Response(results)