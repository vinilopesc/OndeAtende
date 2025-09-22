# Arquivo: apps/triage/routing.py
# Criar novo arquivo:

from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from apps.facilities.models import Facility, MedicalShift, MedicalSpecialty
from apps.triage.models import TriageSession
import logging

logger = logging.getLogger(__name__)


class TriageRouter:
    """
    Sistema inteligente de roteamento pós-triagem
    Considera: urgência Manchester + especialidade necessária + distância + capacidade
    """

    # Mapeamento queixa → especialidades sugeridas
    COMPLAINT_SPECIALTY_MAP = {
        'chest_pain': ['CARDIOLOGIA', 'CLINICA_GERAL', 'EMERGENCIA'],
        'shortness_breath': ['PNEUMOLOGIA', 'CARDIOLOGIA', 'EMERGENCIA'],
        'abdominal_pain': ['GASTRO', 'CIRURGIA', 'CLINICA_GERAL'],
        'headache': ['NEUROLOGIA', 'CLINICA_GERAL'],
        'major_trauma': ['ORTOPEDIA', 'CIRURGIA', 'EMERGENCIA'],
        'fever_child': ['PEDIATRIA', 'EMERGENCIA_PEDIATRICA'],
        'pregnancy_labor': ['OBSTETRICIA', 'GINECOLOGIA'],
    }

    def route_patient(
            self,
            session: TriageSession,
            user_lat: Optional[float] = None,
            user_lng: Optional[float] = None,
            max_results: int = 3
    ) -> List[Dict]:
        """
        Roteia paciente para melhor unidade baseado em triagem

        Returns:
            Lista ordenada com top 3 unidades recomendadas
        """

        # 1. Determina especialidades necessárias
        specialties = self._get_required_specialties(session)

        # 2. Filtra facilities baseado na urgência
        facilities = self._filter_by_urgency(session.priority_color)

        # 3. Filtra por especialidade disponível
        if specialties:
            facilities = self._filter_by_specialty(facilities, specialties)

        # 4. Calcula score para cada facility
        scored_facilities = []
        for facility in facilities:
            score, details = self._calculate_facility_score(
                facility, session, user_lat, user_lng, specialties
            )

            scored_facilities.append({
                'facility': facility,
                'score': score,
                'details': details,
                'recommended_action': self._get_recommendation(session.priority_color, facility)
            })

        # 5. Ordena por score e retorna top N
        scored_facilities.sort(key=lambda x: x['score'], reverse=True)

        results = []
        for item in scored_facilities[:max_results]:
            results.append({
                'facility': {
                    'id': str(item['facility'].id),
                    'name': item['facility'].name,
                    'type': item['facility'].get_facility_type_display(),
                    'address': item['facility'].address,
                    'phone': item['facility'].phone_primary,
                    'emergency_phone': item['facility'].phone_emergency,
                    'latitude': float(item['facility'].latitude),
                    'longitude': float(item['facility'].longitude),
                },
                'score': item['score'],
                'distance_km': item['details'].get('distance'),
                'estimated_wait_minutes': item['details'].get('wait_time'),
                'occupancy_percent': item['facility'].current_occupancy_percent,
                'has_specialty': item['details'].get('has_specialty'),
                'recommendation': item['recommended_action'],
                'route_url': self._generate_route_url(
                    user_lat, user_lng,
                    item['facility'].latitude, item['facility'].longitude
                ) if user_lat and user_lng else None
            })

        # Log de roteamento para auditoria
        logger.info(f"Roteamento triagem {session.id}: {len(results)} unidades sugeridas")

        return results

    def _get_required_specialties(self, session: TriageSession) -> List[str]:
        """Determina especialidades baseado na queixa e discriminadores"""
        base_specialties = self.COMPLAINT_SPECIALTY_MAP.get(
            session.manchester_flowchart, ['CLINICA_GERAL']
        )

        # Adiciona especialidades baseado em discriminadores específicos
        if session.discriminators_answered.get('cardiac_pain'):
            base_specialties.append('CARDIOLOGIA')
        if session.discriminators_answered.get('neurological_deficit'):
            base_specialties.append('NEUROLOGIA')
        if session.discriminators_answered.get('major_bleeding'):
            base_specialties.append('CIRURGIA')

        return list(set(base_specialties))  # Remove duplicatas

    def _filter_by_urgency(self, priority: str) -> models.QuerySet:
        """Filtra unidades apropriadas para o nível de urgência"""
        base_query = Facility.objects.filter(is_active=True)

        if priority == 'RED':
            # Emergência absoluta - apenas hospitais com emergência
            return base_query.filter(
                facility_type__in=['HOSPITAL', 'PS'],
                is_accepting_emergencies=True,
                resources__contains=['sala_vermelha']
            )
        elif priority == 'ORANGE':
            # Muito urgente - hospitais e UPAs com emergência
            return base_query.filter(
                facility_type__in=['HOSPITAL', 'PS', 'UPA'],
                is_accepting_emergencies=True
            )
        elif priority == 'YELLOW':
            # Urgente - UPAs e hospitais
            return base_query.filter(
                facility_type__in=['UPA', 'HOSPITAL', 'PS'],
                Q(is_accepting_emergencies=True) | Q(is_accepting_walkins=True)
            )
        elif priority in ['GREEN', 'BLUE']:
            # Pouco/Não urgente - todas unidades
            return base_query.filter(
                Q(is_accepting_walkins=True) | Q(is_24h=True)
            )

        return base_query

    def _filter_by_specialty(self, facilities, specialties: List[str]):
        """Filtra unidades que têm as especialidades em plantão"""
        now = timezone.now()

        return facilities.filter(
            shifts__specialty__code__in=specialties,
            shifts__shift_date=now.date(),
            shifts__status='ACTIVE'
        ).distinct()

    def _calculate_facility_score(
            self,
            facility: Facility,
            session: TriageSession,
            user_lat: Optional[float],
            user_lng: Optional[float],
            specialties: List[str]
    ) -> Tuple[float, Dict]:
        """
        Calcula score holístico da unidade
        Fatores: distância, ocupação, especialidade, tipo, recursos
        """
        score = 100.0
        details = {}

        # 1. Fator distância (peso alto para emergências)
        if user_lat and user_lng:
            distance = facility.calculate_distance_from(user_lat, user_lng)
            details['distance'] = round(distance, 1)

            if session.priority_color == 'RED':
                score -= distance * 5  # Penaliza muito para emergências
            elif session.priority_color == 'ORANGE':
                score -= distance * 3
            else:
                score -= distance * 1.5

        # 2. Fator ocupação
        occupancy = facility.current_occupancy_percent
        if occupancy > 90:
            score -= 30
        elif occupancy > 70:
            score -= 15
        elif occupancy > 50:
            score -= 5

        # 3. Fator especialidade
        has_specialty = False
        if specialties:
            available_specs = MedicalShift.objects.filter(
                facility=facility,
                specialty__code__in=specialties,
                shift_date=timezone.now().date(),
                status='ACTIVE'
            ).exists()

            if available_specs:
                has_specialty = True
                score += 25  # Bonus por ter especialidade

        details['has_specialty'] = has_specialty

        # 4. Fator tipo de unidade
        if session.priority_color in ['RED', 'ORANGE']:
            if facility.facility_type == 'HOSPITAL':
                score += 20
            elif facility.facility_type == 'PS':
                score += 15
        elif session.priority_color in ['GREEN', 'BLUE']:
            if facility.facility_type == 'UBS':
                score += 10  # Preferir atenção básica para casos simples

        # 5. Fator recursos especiais
        if session.manchester_flowchart == 'chest_pain' and 'hemodinamica' in facility.resources:
            score += 15
        if session.manchester_flowchart == 'major_trauma' and 'centro_trauma' in facility.resources:
            score += 20

        # 6. Tempo de espera estimado
        wait_time = facility.average_wait_time_minutes
        if session.priority_color in ['RED', 'ORANGE']:
            wait_time = min(wait_time, 10)  # Emergências têm prioridade
        details['wait_time'] = wait_time

        return max(0, score), details

    def _get_recommendation(self, priority: str, facility: Facility) -> str:
        """Gera recomendação de ação baseada na prioridade"""
        if priority == 'RED':
            return f"EMERGÊNCIA! Dirija-se IMEDIATAMENTE para {facility.name}. Se possível, ligue 192."
        elif priority == 'ORANGE':
            return f"MUITO URGENTE. Vá rapidamente para {facility.name}. Tempo máximo: 10 minutos."
        elif priority == 'YELLOW':
            return f"Urgente. Dirija-se para {facility.name} nas próximas 60 minutos."
        elif priority == 'GREEN':
            return f"Procure {facility.name} hoje. Tempo estimado de espera: {facility.average_wait_time_minutes} minutos."
        else:  # BLUE
            return f"Não urgente. Considere agendar consulta em {facility.name} ou procurar UBS."

    def _generate_route_url(self, origin_lat, origin_lng, dest_lat, dest_lng) -> str:
        """Gera URL do Google Maps para rota"""
        return f"https://www.google.com/maps/dir/{origin_lat},{origin_lng}/{dest_lat},{dest_lng}"