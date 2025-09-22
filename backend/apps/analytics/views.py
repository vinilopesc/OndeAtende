# apps/analytics/views.py
"""
Views para analytics e dashboards gerenciais
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta
from apps.triage.models import TriageSession
from apps.facilities.models import Facility


class DashboardView(APIView):
    """
    Dashboard principal com métricas em tempo real
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retorna métricas do dashboard"""
        facility_id = request.query_params.get('facility')
        date_from = timezone.now() - timedelta(days=7)

        # Base query
        sessions = TriageSession.objects.filter(
            created_at__gte=date_from
        )

        if facility_id:
            sessions = sessions.filter(facility_id=facility_id)

        # Métricas gerais
        metrics = sessions.aggregate(
            total_patients=Count('id'),
            avg_wait_time=Avg('total_wait_time_minutes'),
            critical_cases=Count('id', filter=Q(priority_color__in=['RED', 'ORANGE'])),
            discharged=Count('id', filter=Q(status='DISCHARGED')),
            left_without_care=Count('id', filter=Q(status='LEFT'))
        )

        # Taxa LWBS
        if metrics['total_patients'] > 0:
            metrics['lwbs_rate'] = (metrics['left_without_care'] / metrics['total_patients']) * 100
        else:
            metrics['lwbs_rate'] = 0

        # Distribuição por prioridade
        priority_distribution = sessions.values('priority_color').annotate(
            count=Count('id')
        ).order_by('priority_color')

        # Tendência diária
        daily_trend = sessions.values('arrival_time__date').annotate(
            total=Count('id'),
            avg_wait=Avg('total_wait_time_minutes')
        ).order_by('arrival_time__date')

        # Top queixas
        top_complaints = sessions.values('manchester_flowchart').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        return Response({
            'metrics': metrics,
            'priority_distribution': list(priority_distribution),
            'daily_trend': list(daily_trend),
            'top_complaints': list(top_complaints),
            'period': {
                'from': date_from.isoformat(),
                'to': timezone.now().isoformat()
            }
        })


class ReportsView(APIView):
    """
    Geração de relatórios gerenciais
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Gera relatório baseado nos parâmetros"""
        report_type = request.query_params.get('type', 'summary')
        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')
        facility_id = request.query_params.get('facility')

        # Parse datas
        if date_from:
            date_from = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
        else:
            date_from = timezone.now().date() - timedelta(days=30)

        if date_to:
            date_to = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
        else:
            date_to = timezone.now().date()

        # Base query
        sessions = TriageSession.objects.filter(
            arrival_time__date__gte=date_from,
            arrival_time__date__lte=date_to
        )

        if facility_id:
            sessions = sessions.filter(facility_id=facility_id)

        if report_type == 'summary':
            return self._generate_summary_report(sessions, date_from, date_to)
        elif report_type == 'performance':
            return self._generate_performance_report(sessions, date_from, date_to)
        elif report_type == 'quality':
            return self._generate_quality_report(sessions, date_from, date_to)
        else:
            return Response({'error': 'Tipo de relatório inválido'}, status=400)

    def _generate_summary_report(self, sessions, date_from, date_to):
        """Relatório resumido"""
        summary = sessions.aggregate(
            total_patients=Count('id'),
            avg_wait_time=Avg('total_wait_time_minutes'),
            avg_door_to_triage=Avg('door_to_triage_minutes'),
            avg_triage_to_care=Avg('triage_to_attendance_minutes'),
            red_cases=Count('id', filter=Q(priority_color='RED')),
            orange_cases=Count('id', filter=Q(priority_color='ORANGE')),
            yellow_cases=Count('id', filter=Q(priority_color='YELLOW')),
            green_cases=Count('id', filter=Q(priority_color='GREEN')),
            blue_cases=Count('id', filter=Q(priority_color='BLUE'))
        )

        return Response({
            'type': 'summary',
            'period': {
                'from': date_from.isoformat(),
                'to': date_to.isoformat()
            },
            'data': summary
        })

    def _generate_performance_report(self, sessions, date_from, date_to):
        """Relatório de performance"""
        # Métricas de performance por facility
        performance = sessions.values('facility__name').annotate(
            total=Count('id'),
            avg_wait=Avg('total_wait_time_minutes'),
            within_target=Count('id', filter=Q(
                priority_color='RED', total_wait_time_minutes__lte=0
            ) | Q(
                priority_color='ORANGE', total_wait_time_minutes__lte=10
            ) | Q(
                priority_color='YELLOW', total_wait_time_minutes__lte=60
            ) | Q(
                priority_color='GREEN', total_wait_time_minutes__lte=120
            ) | Q(
                priority_color='BLUE', total_wait_time_minutes__lte=240
            ))
        ).order_by('-total')

        return Response({
            'type': 'performance',
            'period': {
                'from': date_from.isoformat(),
                'to': date_to.isoformat()
            },
            'data': list(performance)
        })

    def _generate_quality_report(self, sessions, date_from, date_to):
        """Relatório de qualidade"""
        quality_metrics = {
            'lwbs_rate': sessions.filter(status='LEFT').count() / max(sessions.count(), 1) * 100,
            'readmission_rate': 0,  # Implementar lógica de readmissão
            'manchester_compliance': sessions.exclude(priority_color='').count() / max(sessions.count(), 1) * 100,
            'avg_patient_satisfaction': 4.2,  # Placeholder - integrar com sistema de feedback
        }

        return Response({
            'type': 'quality',
            'period': {
                'from': date_from.isoformat(),
                'to': date_to.isoformat()
            },
            'data': quality_metrics
        })