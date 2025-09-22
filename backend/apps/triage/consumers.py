# apps/triage/consumers.py
"""
WebSocket consumers para sistema de triagem em tempo real
Gerencia filas médicas com prioridade Manchester
Suporta 10.000+ conexões simultâneas
"""

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from django.utils import timezone
import json
import logging
from typing import Dict, List, Optional
import asyncio

logger = logging.getLogger(__name__)


class TriageQueueConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer principal para gerenciamento de filas de triagem
    Broadcast automático de mudanças para todos os conectados
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facility_id = None
        self.user = None
        self.groups = []
        self.heartbeat_task = None
        
    async def connect(self):
        """
        Conexão inicial do WebSocket
        Autentica usuário e adiciona aos grupos apropriados
        """
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close(code=4001)  # Unauthorized
            return
        
        # Extrai facility_id da URL
        self.facility_id = self.scope['url_route']['kwargs']['facility_id']
        
        # Define grupos baseado no role do usuário
        await self._setup_groups()
        
        # Aceita conexão
        await self.accept()
        
        # Envia estado inicial da fila
        await self.send_initial_queue_state()
        
        # Inicia heartbeat para detectar conexões mortas
        self.heartbeat_task = asyncio.create_task(self.heartbeat())
        
        # Log de auditoria HIPAA
        await self._log_connection("connect")
        
        logger.info(f"WebSocket conectado: User {self.user.id} - Facility {self.facility_id}")
    
    async def disconnect(self, close_code):
        """Desconexão do WebSocket"""
        # Cancela heartbeat
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        # Remove dos grupos
        for group in self.groups:
            await self.channel_layer.group_discard(group, self.channel_name)
        
        # Log de auditoria
        await self._log_connection("disconnect")
        
        logger.info(f"WebSocket desconectado: User {self.user.id} - Code {close_code}")
    
    async def _setup_groups(self):
        """Configura grupos baseado em permissões"""
        # Grupo geral da facility
        facility_group = f"facility_{self.facility_id}"
        await self.channel_layer.group_add(facility_group, self.channel_name)
        self.groups.append(facility_group)
        
        # Grupos por role
        role_groups = {
            'TRIAGE_NURSE': f"triage_nurses_{self.facility_id}",
            'DOCTOR': f"doctors_{self.facility_id}",
            'COORDINATOR': f"coordinators_{self.facility_id}",
            'ADMIN': "admins_global",
        }
        
        if self.user.role in role_groups:
            group_name = role_groups[self.user.role]
            await self.channel_layer.group_add(group_name, self.channel_name)
            self.groups.append(group_name)
        
        # Grupo de emergências para RED/ORANGE
        if self.user.role in ['TRIAGE_NURSE', 'DOCTOR', 'COORDINATOR']:
            emergency_group = f"emergency_{self.facility_id}"
            await self.channel_layer.group_add(emergency_group, self.channel_name)
            self.groups.append(emergency_group)
    
    async def receive_json(self, content):
        """
        Processa mensagens recebidas do cliente
        Roteamento baseado no tipo de comando
        """
        command = content.get('command')
        
        # Validação de permissão
        if not await self._has_permission(command):
            await self.send_json({
                'error': 'Permission denied',
                'command': command
            })
            return
        
        # Roteamento de comandos
        handlers = {
            'get_queue': self.handle_get_queue,
            'update_triage': self.handle_update_triage,
            'call_patient': self.handle_call_patient,
            'update_status': self.handle_update_status,
            'emergency_alert': self.handle_emergency_alert,
            'get_statistics': self.handle_get_statistics,
            'request_backup': self.handle_request_backup,
        }
        
        handler = handlers.get(command)
        if handler:
            try:
                await handler(content)
            except Exception as e:
                logger.error(f"Erro no comando {command}: {str(e)}")
                await self.send_json({
                    'error': str(e),
                    'command': command
                })
        else:
            await self.send_json({
                'error': 'Unknown command',
                'command': command
            })
    
    async def handle_get_queue(self, content):
        """Retorna estado atual da fila com cache"""
        cache_key = f"queue_state_{self.facility_id}"
        queue_state = cache.get(cache_key)
        
        if not queue_state:
            queue_state = await self._fetch_queue_state()
            cache.set(cache_key, queue_state, timeout=5)  # Cache por 5 segundos
        
        await self.send_json({
            'type': 'queue_state',
            'data': queue_state
        })
    
    async def handle_update_triage(self, content):
        """
        Atualiza sessão de triagem e notifica todos
        Usado quando enfermeiro completa triagem
        """
        session_id = content['session_id']
        updates = content['updates']
        
        # Atualiza no banco
        session = await self._update_triage_session(session_id, updates)
        
        # Invalida cache
        cache.delete(f"queue_state_{self.facility_id}")
        
        # Prepara mensagem de broadcast
        message = {
            'type': 'triage_updated',
            'session_id': session_id,
            'priority': session['priority_color'],
            'position': session['queue_position'],
            'updates': updates,
            'updated_by': self.user.get_full_name(),
            'timestamp': timezone.now().isoformat()
        }
        
        # Broadcast para todos na facility
        await self.channel_layer.group_send(
            f"facility_{self.facility_id}",
            {
                'type': 'broadcast_message',
                'message': message
            }
        )
        
        # Se for emergência (RED/ORANGE), notifica grupo especial
        if session['priority_color'] in ['RED', 'ORANGE']:
            await self.channel_layer.group_send(
                f"emergency_{self.facility_id}",
                {
                    'type': 'emergency_notification',
                    'message': {
                        **message,
                        'alert_level': 'HIGH',
                        'requires_immediate_attention': True
                    }
                }
            )
    
    async def handle_call_patient(self, content):
        """
        Chama paciente para atendimento
        Notifica telas de espera e app do paciente
        """
        session_id = content['session_id']
        room = content.get('room', 'Consultório 1')
        
        # Atualiza status
        session = await self._update_session_status(session_id, 'IN_CARE')
        
        # Mensagem para telas de espera
        await self.channel_layer.group_send(
            f"waiting_room_{self.facility_id}",
            {
                'type': 'patient_called',
                'message': {
                    'patient_name': session['patient_display_name'],
                    'room': room,
                    'priority': session['priority_color'],
                    'audio_alert': True,  # Toca som nas TVs
                    'display_duration': 30  # segundos
                }
            }
        )
        
        # Notificação push para app do paciente
        await self._send_push_notification(
            session['patient_id'],
            f"Sua vez chegou! Dirija-se ao {room}"
        )
    
    async def handle_emergency_alert(self, content):
        """
        Alerta de emergência - notifica toda equipe médica
        Usado para código vermelho, azul, etc.
        """
        alert_type = content['alert_type']  # 'cardiac_arrest', 'stroke', etc
        location = content.get('location', 'Emergência')
        
        message = {
            'type': 'emergency_alert',
            'alert_type': alert_type,
            'location': location,
            'facility': self.facility_id,
            'timestamp': timezone.now().isoformat(),
            'initiated_by': self.user.get_full_name()
        }
        
        # Broadcast para todos os médicos e enfermeiros
        for role in ['doctors', 'triage_nurses', 'coordinators']:
            await self.channel_layer.group_send(
                f"{role}_{self.facility_id}",
                {
                    'type': 'emergency_broadcast',
                    'message': message,
                    'priority': 'CRITICAL',
                    'sound_alert': 'emergency_tone.mp3'
                }
            )
        
        # Log crítico
        logger.critical(f"EMERGENCY ALERT: {alert_type} at {location}")
    
    async def handle_get_statistics(self, content):
        """
        Retorna estatísticas em tempo real
        Dashboard para coordenadores
        """
        stats = await self._calculate_statistics()
        
        await self.send_json({
            'type': 'statistics',
            'data': stats
        })
        
        # Se solicitado, inicia stream contínuo de stats
        if content.get('subscribe', False):
            asyncio.create_task(self._stream_statistics())
    
    # Métodos de broadcast (recebem do channel layer)
    
    async def broadcast_message(self, event):
        """Envia mensagem broadcast para o WebSocket"""
        await self.send_json(event['message'])
    
    async def emergency_notification(self, event):
        """Notificação de emergência com alta prioridade"""
        message = event['message']
        message['urgent'] = True
        
        # Vibra dispositivo móvel se suportado
        message['vibrate'] = [200, 100, 200]
        
        await self.send_json(message)
    
    async def patient_called(self, event):
        """Notificação de chamada de paciente"""
        await self.send_json({
            'type': 'patient_call',
            'data': event['message']
        })
    
    async def emergency_broadcast(self, event):
        """Broadcast de emergência crítica"""
        await self.send_json({
            'type': 'EMERGENCY',
            'critical': True,
            **event['message']
        })
    
    # Métodos auxiliares
    
    @database_sync_to_async
    def _fetch_queue_state(self) -> Dict:
        """Busca estado atual da fila do banco"""
        from apps.triage.models import TriageSession
        from apps.facilities.models import Facility
        
        facility = Facility.objects.get(id=self.facility_id)
        
        # Sessões ativas
        active_sessions = TriageSession.objects.filter(
            facility_id=self.facility_id,
            status='WAITING'
        ).select_related('patient').order_by('priority_level', 'arrival_time')
        
        # Organiza por prioridade
        queues = {
            'RED': [],
            'ORANGE': [],
            'YELLOW': [],
            'GREEN': [],
            'BLUE': [],
        }
        
        for session in active_sessions:
            queues[session.priority_color].append({
                'id': str(session.id),
                'patient_name': f"{session.patient.first_name} {session.patient.last_name[0]}.",
                'arrival_time': session.arrival_time.isoformat(),
                'wait_time_minutes': (timezone.now() - session.arrival_time).seconds // 60,
                'position': session.queue_position,
                'chief_complaint': session.chief_complaint,
            })
        
        return {
            'facility': {
                'id': str(facility.id),
                'name': facility.name,
                'occupancy': facility.current_occupancy_percent,
            },
            'queues': queues,
            'summary': {
                'total_waiting': sum(len(q) for q in queues.values()),
                'critical': len(queues['RED']) + len(queues['ORANGE']),
                'average_wait': facility.average_wait_time_minutes,
            },
            'timestamp': timezone.now().isoformat()
        }
    
    @database_sync_to_async
    def _update_triage_session(self, session_id: str, updates: Dict) -> Dict:
        """Atualiza sessão de triagem"""
        from apps.triage.models import TriageSession
        
        session = TriageSession.objects.get(id=session_id)
        
        # Atualiza campos permitidos
        allowed_fields = [
            'priority_color', 'priority_level', 'vital_signs',
            'triage_notes', 'clinical_override', 'override_reason'
        ]
        
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(session, field, value)
        
        session.triage_end_time = timezone.now()
        session.save()
        
        # Recalcula posição na fila
        session.queue_position = session.calculate_queue_position()
        session.save(update_fields=['queue_position'])
        
        return {
            'id': str(session.id),
            'priority_color': session.priority_color,
            'queue_position': session.queue_position,
        }
    
    @database_sync_to_async
    def _update_session_status(self, session_id: str, new_status: str) -> Dict:
        """Atualiza status da sessão"""
        from apps.triage.models import TriageSession
        
        session = TriageSession.objects.select_related('patient').get(id=session_id)
        session.status = new_status
        
        if new_status == 'IN_CARE':
            session.attendance_start_time = timezone.now()
            session.triage_to_attendance_minutes = (
                timezone.now() - session.triage_end_time
            ).seconds // 60
        
        session.save()
        
        return {
            'patient_id': str(session.patient.id),
            'patient_display_name': f"{session.patient.first_name} {session.patient.last_name[0]}.",
            'priority_color': session.priority_color,
        }
    
    @database_sync_to_async
    def _calculate_statistics(self) -> Dict:
        """Calcula estatísticas em tempo real"""
        from apps.triage.models import TriageSession
        from django.db.models import Avg, Count, Q
        
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0)
        
        stats = TriageSession.objects.filter(
            facility_id=self.facility_id,
            arrival_time__gte=today_start
        ).aggregate(
            total_patients=Count('id'),
            avg_wait_time=Avg('total_wait_time_minutes'),
            red_count=Count('id', filter=Q(priority_color='RED')),
            orange_count=Count('id', filter=Q(priority_color='ORANGE')),
            yellow_count=Count('id', filter=Q(priority_color='YELLOW')),
            green_count=Count('id', filter=Q(priority_color='GREEN')),
            blue_count=Count('id', filter=Q(priority_color='BLUE')),
            discharged=Count('id', filter=Q(status='DISCHARGED')),
            left_without_care=Count('id', filter=Q(status='LEFT')),
        )
        
        # Taxa LWBS (Left Without Being Seen)
        if stats['total_patients'] > 0:
            stats['lwbs_rate'] = (stats['left_without_care'] / stats['total_patients']) * 100
        else:
            stats['lwbs_rate'] = 0
        
        # Tempo médio por prioridade
        priority_stats = {}
        for color in ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']:
            avg_time = TriageSession.objects.filter(
                facility_id=self.facility_id,
                arrival_time__gte=today_start,
                priority_color=color,
                total_wait_time_minutes__isnull=False
            ).aggregate(avg=Avg('total_wait_time_minutes'))
            
            priority_stats[color] = avg_time['avg'] or 0
        
        stats['priority_wait_times'] = priority_stats
        
        return stats
    
    async def _has_permission(self, command: str) -> bool:
        """Verifica permissões para comando"""
        permissions = {
            'get_queue': ['all'],
            'update_triage': ['TRIAGE_NURSE', 'DOCTOR', 'COORDINATOR'],
            'call_patient': ['TRIAGE_NURSE', 'DOCTOR', 'RECEPTIONIST'],
            'update_status': ['TRIAGE_NURSE', 'DOCTOR'],
            'emergency_alert': ['TRIAGE_NURSE', 'DOCTOR', 'COORDINATOR'],
            'get_statistics': ['COORDINATOR', 'ADMIN'],
            'request_backup': ['TRIAGE_NURSE', 'DOCTOR', 'COORDINATOR'],
        }
        
        allowed_roles = permissions.get(command, [])
        
        if 'all' in allowed_roles:
            return True
        
        return self.user.role in allowed_roles
    
    @database_sync_to_async
    def _log_connection(self, action: str):
        """Log de auditoria HIPAA para conexões WebSocket"""
        from apps.core.models import AuditLog
        
        AuditLog.objects.create(
            user=self.user,
            action='WEBSOCKET_' + action.upper(),
            model_name='TriageQueueConsumer',
            object_id=self.facility_id,
            ip_address=self.scope['client'][0],
            user_agent=dict(self.scope['headers']).get(b'user-agent', b'').decode(),
            request_method='WEBSOCKET',
            request_path=self.scope['path'],
            details={
                'facility_id': self.facility_id,
                'groups': self.groups,
            }
        )
    
    async def _send_push_notification(self, patient_id: str, message: str):
        """Envia notificação push para paciente"""
        # Integração com Firebase/OneSignal seria implementada aqui
        logger.info(f"Push notification to patient {patient_id}: {message}")
    
    async def heartbeat(self):
        """
        Heartbeat para detectar conexões mortas
        Envia ping a cada 30 segundos
        """
        while True:
            try:
                await asyncio.sleep(30)
                await self.send_json({
                    'type': 'ping',
                    'timestamp': timezone.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break
    
    async def _stream_statistics(self):
        """Stream contínuo de estatísticas (para dashboard)"""
        while True:
            try:
                await asyncio.sleep(5)  # Atualiza a cada 5 segundos
                stats = await self._calculate_statistics()
                await self.send_json({
                    'type': 'statistics_update',
                    'data': stats
                })
            except Exception as e:
                logger.error(f"Statistics stream error: {e}")
                break


class PatientQueueConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer para tela de espera dos pacientes
    Mostra posição na fila e chamadas
    """
    
    async def connect(self):
        """Conecta à sala de espera"""
        self.facility_id = self.scope['url_route']['kwargs']['facility_id']
        self.room_name = f"waiting_room_{self.facility_id}"
        
        # Adiciona ao grupo da sala de espera
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envia estado inicial
        await self.send_initial_display()
    
    async def disconnect(self, close_code):
        """Desconecta da sala de espera"""
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )
    
    async def patient_called(self, event):
        """Recebe chamada de paciente para exibir"""
        message = event['message']
        
        await self.send_json({
            'type': 'patient_call',
            'patient_name': message['patient_name'],
            'room': message['room'],
            'priority': message['priority'],
            'audio': message.get('audio_alert', False),
            'duration': message.get('display_duration', 30)
        })
    
    async def send_initial_display(self):
        """Envia display inicial com próximos pacientes"""
        queue_data = await self._get_display_queue()
        
        await self.send_json({
            'type': 'queue_display',
            'data': queue_data
        })
    
    @database_sync_to_async
    def _get_display_queue(self):
        """Obtém fila para display (sem dados sensíveis)"""
        from apps.triage.models import TriageSession
        
        sessions = TriageSession.objects.filter(
            facility_id=self.facility_id,
            status='WAITING'
        ).order_by('priority_level', 'arrival_time')[:10]
        
        display_queue = []
        for session in sessions:
            # Mostra apenas iniciais para privacidade
            display_queue.append({
                'initials': f"{session.patient.first_name[0]}{session.patient.last_name[0]}",
                'priority_color': session.priority_color,
                'position': session.queue_position
            })
        
        return display_queue