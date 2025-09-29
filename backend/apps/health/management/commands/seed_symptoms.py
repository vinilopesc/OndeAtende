from django.core.management.base import BaseCommand
from apps.health.models import Symptom, ManchesterProtocol


class Command(BaseCommand):
    help = 'Popula base com sintomas do protocolo Manchester'

    def handle(self, *args, **options):
        symptoms_data = [
            # Emergência (Vermelho)
            ('Parada respiratória', 'Ausência de respiração', ManchesterProtocol.RED, 'parada,respiratória,emergência'),
            ('Dor torácica intensa', 'Dor no peito com sudorese e falta de ar', ManchesterProtocol.RED,
             'dor,peito,torácica,infarto'),
            ('Convulsão ativa', 'Convulsão em andamento', ManchesterProtocol.RED, 'convulsão,epilepsia'),
            ('Hemorragia grave', 'Sangramento intenso não controlado', ManchesterProtocol.RED,
             'sangramento,hemorragia'),

            # Muito Urgente (Laranja)
            ('Dor abdominal aguda', 'Dor intensa na barriga', ManchesterProtocol.ORANGE, 'dor,barriga,abdominal'),
            ('Dispneia moderada', 'Dificuldade para respirar', ManchesterProtocol.ORANGE, 'falta,ar,dispneia'),
            ('Febre alta', 'Temperatura acima de 39°C', ManchesterProtocol.ORANGE, 'febre,temperatura'),

            # Urgente (Amarelo)
            ('Vômito persistente', 'Vômitos repetidos', ManchesterProtocol.YELLOW, 'vômito,enjoo,náusea'),
            ('Dor moderada', 'Dor suportável mas incômoda', ManchesterProtocol.YELLOW, 'dor,moderada'),
            ('Ferimento', 'Corte ou ferida que precisa sutura', ManchesterProtocol.YELLOW, 'corte,ferida,machucado'),

            # Pouco Urgente (Verde)
            ('Resfriado', 'Sintomas gripais leves', ManchesterProtocol.GREEN, 'gripe,resfriado,coriza'),
            ('Dor de cabeça leve', 'Cefaleia sem outros sintomas', ManchesterProtocol.GREEN, 'dor,cabeça,cefaleia'),
            ('Tosse seca', 'Tosse sem febre ou falta de ar', ManchesterProtocol.GREEN, 'tosse'),

            # Não Urgente (Azul)
            ('Renovação de receita', 'Necessita apenas prescrição', ManchesterProtocol.BLUE, 'receita,medicamento'),
            ('Exame de rotina', 'Check-up sem sintomas', ManchesterProtocol.BLUE, 'exame,rotina,check-up'),
        ]

        created = 0
        for name, desc, priority, keywords in symptoms_data:
            symptom, is_new = Symptom.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'base_priority': priority,
                    'keywords': keywords
                }
            )
            if is_new:
                created += 1

        self.stdout.write(f'✓ {created} sintomas criados')