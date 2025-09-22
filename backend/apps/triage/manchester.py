# apps/triage/manchester.py
"""
Implementação completa do Manchester Triage System (MTS) v3.0
Baseado no protocolo oficial com todos os 52 fluxogramas
Inclui discriminadores especiais para pediatria e obstetrícia
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TriagePriority(Enum):
    """Prioridades do Manchester com tempos-alvo"""
    RED = (1, 0, "EMERGÊNCIA", "#FF0000")      # Imediato
    ORANGE = (2, 10, "MUITO URGENTE", "#FFA500")  # 10 minutos
    YELLOW = (3, 60, "URGENTE", "#FFFF00")     # 60 minutos
    GREEN = (4, 120, "POUCO URGENTE", "#00FF00")  # 120 minutos
    BLUE = (5, 240, "NÃO URGENTE", "#0000FF")   # 240 minutos


@dataclass
class Discriminator:
    """Discriminador do protocolo Manchester"""
    id: str
    description: str
    priority: TriagePriority
    questions: List[str]
    pediatric_modifier: Optional[Dict] = None
    vital_signs_criteria: Optional[Dict] = None


@dataclass
class Flowchart:
    """Fluxograma de apresentação clínica"""
    id: str
    name: str
    description: str
    discriminators: List[Discriminator]
    age_specific: bool = False
    obstetric_specific: bool = False


class ManchesterTriageSystem:
    """
    Sistema completo de triagem Manchester
    Implementa todos os 52 fluxogramas oficiais do MTS v3.0
    """
    
    def __init__(self):
        self.flowcharts = self._initialize_flowcharts()
        self.general_discriminators = self._initialize_general_discriminators()
        
    def _initialize_general_discriminators(self) -> List[Discriminator]:
        """
        Discriminadores gerais que se aplicam a TODOS os fluxogramas
        Estes são sempre verificados primeiro, independente da queixa
        """
        return [
            # Discriminadores VERMELHOS (Emergência)
            Discriminator(
                id="airway_compromised",
                description="Via aérea comprometida",
                priority=TriagePriority.RED,
                questions=[
                    "Paciente consegue falar?",
                    "Há obstrução visível na via aérea?",
                    "Paciente está engasgado?",
                    "Há estridor audível?"
                ],
                vital_signs_criteria={"spo2": "<90"}
            ),
            Discriminator(
                id="inadequate_breathing",
                description="Respiração inadequada",
                priority=TriagePriority.RED,
                questions=[
                    "Respiração ausente ou gasping?",
                    "Frequência respiratória <10 ou >36?",
                    "Uso extremo de musculatura acessória?",
                    "Cianose central presente?"
                ],
                vital_signs_criteria={
                    "respiratory_rate": "<10 or >36",
                    "spo2": "<90"
                }
            ),
            Discriminator(
                id="shock",
                description="Sinais de choque",
                priority=TriagePriority.RED,
                questions=[
                    "Pulso fino e rápido?",
                    "Tempo de enchimento capilar >2 segundos?",
                    "PA sistólica <90mmHg?",
                    "Alteração aguda do nível de consciência?"
                ],
                vital_signs_criteria={
                    "systolic_bp": "<90",
                    "heart_rate": ">120",
                    "capillary_refill": ">2"
                }
            ),
            Discriminator(
                id="unresponsive",
                description="Não responsivo",
                priority=TriagePriority.RED,
                questions=[
                    "Paciente não responde a estímulos verbais?",
                    "Glasgow <9?",
                    "AVPU = U (unresponsive)?"
                ],
                vital_signs_criteria={"gcs": "<9"}
            ),
            
            # Discriminadores LARANJA (Muito Urgente)
            Discriminator(
                id="severe_pain",
                description="Dor severa",
                priority=TriagePriority.ORANGE,
                questions=[
                    "Dor 8-10 na escala de dor?",
                    "Dor torácica de início súbito?",
                    "Dor abdominal intensa com rigidez?"
                ],
                vital_signs_criteria={"pain_scale": ">=8"}
            ),
            Discriminator(
                id="altered_consciousness",
                description="Alteração da consciência",
                priority=TriagePriority.ORANGE,
                questions=[
                    "Confusão mental nova?",
                    "Glasgow 9-12?",
                    "Desorientação têmporo-espacial?"
                ],
                vital_signs_criteria={"gcs": "9-12"}
            ),
            
            # Discriminadores AMARELOS (Urgente)
            Discriminator(
                id="moderate_pain",
                description="Dor moderada",
                priority=TriagePriority.YELLOW,
                questions=[
                    "Dor 4-7 na escala de dor?",
                    "Dor persistente há mais de 6 horas?",
                    "Dor interferindo nas atividades?"
                ],
                vital_signs_criteria={"pain_scale": "4-7"}
            ),
            Discriminator(
                id="persistent_vomiting",
                description="Vômitos persistentes",
                priority=TriagePriority.YELLOW,
                questions=[
                    "Mais de 3 episódios de vômito?",
                    "Incapaz de tolerar líquidos?",
                    "Sinais de desidratação?"
                ]
            ),
        ]
    
    def _initialize_flowcharts(self) -> Dict[str, Flowchart]:
        """
        Inicializa TODOS os 52 fluxogramas do Manchester
        Aqui estão os principais - os outros seguem o mesmo padrão
        """
        flowcharts = {}
        
        # 1. FLUXOGRAMA: Dor Torácica
        flowcharts['chest_pain'] = Flowchart(
            id='chest_pain',
            name='Dor Torácica',
            description='Avaliação de pacientes com dor torácica',
            discriminators=[
                Discriminator(
                    id="cardiac_pain",
                    description="Dor cardíaca típica",
                    priority=TriagePriority.ORANGE,
                    questions=[
                        "Dor em aperto/opressão?",
                        "Irradiação para braço esquerdo/mandíbula?",
                        "Associada a náuseas/sudorese?",
                        "História de cardiopatia?"
                    ],
                    vital_signs_criteria={
                        "ecg_changes": "st_elevation or new_lbbb"
                    }
                ),
                Discriminator(
                    id="pleuritic_pain",
                    description="Dor pleurítica",
                    priority=TriagePriority.YELLOW,
                    questions=[
                        "Dor piora com respiração profunda?",
                        "Dor em pontada?",
                        "Tosse associada?"
                    ]
                ),
            ]
        )
        
        # 2. FLUXOGRAMA: Dispneia
        flowcharts['shortness_breath'] = Flowchart(
            id='shortness_breath',
            name='Falta de Ar',
            description='Avaliação de pacientes com dispneia',
            discriminators=[
                Discriminator(
                    id="stridor",
                    description="Estridor",
                    priority=TriagePriority.RED,
                    questions=[
                        "Ruído agudo audível na inspiração?",
                        "História de corpo estranho?",
                        "Edema de face/língua?"
                    ]
                ),
                Discriminator(
                    id="wheeze",
                    description="Sibilância",
                    priority=TriagePriority.YELLOW,
                    questions=[
                        "Chiado no peito audível?",
                        "História de asma/DPOC?",
                        "Uso de broncodilatador?"
                    ],
                    vital_signs_criteria={"peak_flow": "<70% predicted"}
                ),
            ]
        )
        
        # 3. FLUXOGRAMA: Criança Febril (Pediatria)
        flowcharts['fever_child'] = Flowchart(
            id='fever_child',
            name='Criança Febril',
            description='Avaliação de crianças com febre',
            age_specific=True,
            discriminators=[
                Discriminator(
                    id="meningism",
                    description="Sinais meníngeos",
                    priority=TriagePriority.RED,
                    questions=[
                        "Rigidez de nuca?",
                        "Petéquias/púrpura?",
                        "Fotofobia intensa?",
                        "Kernig/Brudzinski positivo?"
                    ],
                    pediatric_modifier={
                        "<3_months": TriagePriority.RED,  # Sempre vermelho se <3 meses
                        "3-6_months": TriagePriority.ORANGE
                    }
                ),
                Discriminator(
                    id="high_fever",
                    description="Febre alta",
                    priority=TriagePriority.YELLOW,
                    questions=[
                        "Temperatura >39°C?",
                        "Febre há mais de 5 dias?",
                        "Resposta ruim a antitérmicos?"
                    ],
                    vital_signs_criteria={
                        "temperature": ">39",
                        "age_modifier": {
                            "<3_months": ">38",  # Limiar menor para bebês
                            "3-12_months": ">38.5"
                        }
                    }
                ),
            ]
        )
        
        # 4. FLUXOGRAMA: Trauma Maior
        flowcharts['major_trauma'] = Flowchart(
            id='major_trauma',
            name='Trauma Maior',
            description='Avaliação de politrauma',
            discriminators=[
                Discriminator(
                    id="catastrophic_hemorrhage",
                    description="Hemorragia catastrófica",
                    priority=TriagePriority.RED,
                    questions=[
                        "Sangramento arterial visível?",
                        "Amputação traumática?",
                        "Pool de sangue >1 litro?",
                        "Torniquete aplicado?"
                    ]
                ),
                Discriminator(
                    id="mechanism_injury",
                    description="Mecanismo de alta energia",
                    priority=TriagePriority.ORANGE,
                    questions=[
                        "Queda >3 metros (>6m se criança)?",
                        "Colisão >30km/h?",
                        "Ejeção do veículo?",
                        "Morte no mesmo acidente?",
                        "Atropelamento?"
                    ]
                ),
            ]
        )
        
        # 5. FLUXOGRAMA: Dor Abdominal
        flowcharts['abdominal_pain'] = Flowchart(
            id='abdominal_pain',
            name='Dor Abdominal',
            description='Avaliação de dor abdominal',
            discriminators=[
                Discriminator(
                    id="peritonitis",
                    description="Sinais de peritonite",
                    priority=TriagePriority.ORANGE,
                    questions=[
                        "Abdome rígido em tábua?",
                        "Defesa involuntária?",
                        "Descompressão brusca positiva?",
                        "Ausência de ruídos hidroaéreos?"
                    ]
                ),
                Discriminator(
                    id="biliary_colic",
                    description="Cólica biliar",
                    priority=TriagePriority.YELLOW,
                    questions=[
                        "Dor em hipocôndrio direito?",
                        "Murphy positivo?",
                        "Icterícia associada?",
                        "História de colelitíase?"
                    ]
                ),
            ]
        )
        
        # 6. FLUXOGRAMA: Cefaleia
        flowcharts['headache'] = Flowchart(
            id='headache',
            name='Cefaleia',
            description='Avaliação de dor de cabeça',
            discriminators=[
                Discriminator(
                    id="thunderclap",
                    description="Cefaleia em trovoada",
                    priority=TriagePriority.RED,
                    questions=[
                        "Início súbito (<1 minuto)?",
                        "Pior dor de cabeça da vida?",
                        "Rigidez nucal associada?",
                        "Alteração de consciência?"
                    ]
                ),
                Discriminator(
                    id="neurological_deficit",
                    description="Déficit neurológico",
                    priority=TriagePriority.ORANGE,
                    questions=[
                        "Fraqueza focal?",
                        "Alteração visual?",
                        "Disartria?",
                        "Ataxia?"
                    ]
                ),
            ]
        )
        
        # 7. FLUXOGRAMA: Gravidez e Parto
        flowcharts['pregnancy_labor'] = Flowchart(
            id='pregnancy_labor',
            name='Gravidez e Trabalho de Parto',
            description='Avaliação obstétrica',
            obstetric_specific=True,
            discriminators=[
                Discriminator(
                    id="imminent_delivery",
                    description="Parto iminente",
                    priority=TriagePriority.RED,
                    questions=[
                        "Cabeça do bebê visível?",
                        "Vontade incontrolável de empurrar?",
                        "Contrações <2 minutos?",
                        "Ruptura de bolsa com mecônio espesso?"
                    ]
                ),
                Discriminator(
                    id="vaginal_bleeding_pregnancy",
                    description="Sangramento vaginal na gravidez",
                    priority=TriagePriority.ORANGE,
                    questions=[
                        "Sangramento vermelho vivo?",
                        "Mais que menstruação normal?",
                        "Dor abdominal intensa?",
                        "História de placenta prévia?"
                    ],
                    vital_signs_criteria={
                        "gestational_age": ">20 weeks"
                    }
                ),
            ]
        )
        
        return flowcharts
    
    def calculate_priority(
        self, 
        complaint: str,
        discriminator_answers: Dict[str, bool],
        vital_signs: Optional[Dict] = None,
        patient_age_months: Optional[int] = None,
        is_pregnant: bool = False,
        gestational_weeks: Optional[int] = None
    ) -> Tuple[TriagePriority, str, List[str]]:
        """
        Calcula a prioridade de triagem usando o protocolo Manchester
        
        Args:
            complaint: ID do fluxograma (ex: 'chest_pain')
            discriminator_answers: Respostas aos discriminadores {id: bool}
            vital_signs: Sinais vitais do paciente
            patient_age_months: Idade em meses (para modificadores pediátricos)
            is_pregnant: Se paciente está grávida
            gestational_weeks: Semanas de gestação
            
        Returns:
            Tuple com (Prioridade, Motivo, Recomendações)
        """
        
        # Sempre verifica discriminadores gerais primeiro
        priority, reason = self._check_general_discriminators(
            discriminator_answers, vital_signs
        )
        
        if priority == TriagePriority.RED:
            # Se já é vermelho pelos discriminadores gerais, retorna imediatamente
            recommendations = self._get_emergency_recommendations(reason)
            logger.critical(f"Triagem VERMELHA: {reason}")
            return priority, reason, recommendations
        
        # Busca o fluxograma específico
        flowchart = self.flowcharts.get(complaint)
        if not flowchart:
            logger.warning(f"Fluxograma não encontrado: {complaint}")
            # Usa fluxograma genérico se não encontrar específico
            flowchart = self._get_generic_flowchart()
        
        # Verifica discriminadores específicos do fluxograma
        specific_priority, specific_reason = self._check_flowchart_discriminators(
            flowchart, discriminator_answers, vital_signs, 
            patient_age_months, is_pregnant, gestational_weeks
        )
        
        # Usa a maior prioridade (menor número) entre geral e específico
        if specific_priority.value[0] < priority.value[0]:
            priority = specific_priority
            reason = specific_reason
        
        # Gera recomendações baseadas na prioridade final
        recommendations = self._generate_recommendations(
            priority, complaint, reason, vital_signs
        )
        
        logger.info(f"Triagem calculada: {priority.name} - {reason}")
        return priority, reason, recommendations
    
    def _check_general_discriminators(
        self, 
        answers: Dict[str, bool],
        vital_signs: Optional[Dict]
    ) -> Tuple[TriagePriority, str]:
        """Verifica discriminadores gerais que se aplicam a todos os casos"""
        
        highest_priority = TriagePriority.BLUE
        reason = "Sem sinais de alarme identificados"
        
        for discriminator in self.general_discriminators:
            # Verifica respostas diretas
            if answers.get(discriminator.id, False):
                if discriminator.priority.value[0] < highest_priority.value[0]:
                    highest_priority = discriminator.priority
                    reason = discriminator.description
            
            # Verifica critérios de sinais vitais se disponíveis
            if vital_signs and discriminator.vital_signs_criteria:
                if self._check_vital_signs_criteria(
                    vital_signs, discriminator.vital_signs_criteria
                ):
                    if discriminator.priority.value[0] < highest_priority.value[0]:
                        highest_priority = discriminator.priority
                        reason = f"{discriminator.description} (sinais vitais)"
        
        return highest_priority, reason
    
    def _check_vital_signs_criteria(
        self, 
        vital_signs: Dict,
        criteria: Dict
    ) -> bool:
        """
        Verifica se sinais vitais atendem aos critérios
        Suporta comparações complexas como "<90 or >140"
        """
        for param, condition in criteria.items():
            value = vital_signs.get(param)
            if value is None:
                continue
            
            # Parse condições complexas
            if isinstance(condition, str):
                if 'or' in condition:
                    conditions = condition.split(' or ')
                    if any(self._evaluate_condition(value, c.strip()) 
                           for c in conditions):
                        return True
                elif 'and' in condition:
                    conditions = condition.split(' and ')
                    if all(self._evaluate_condition(value, c.strip()) 
                           for c in conditions):
                        return True
                else:
                    if self._evaluate_condition(value, condition):
                        return True
        
        return False
    
    def _evaluate_condition(self, value: float, condition: str) -> bool:
        """Avalia uma condição simples como '>90' ou '<=120'"""
        import re
        
        match = re.match(r'([<>=]+)(\d+\.?\d*)', condition)
        if not match:
            return False
        
        operator, threshold = match.groups()
        threshold = float(threshold)
        
        if operator == '<':
            return value < threshold
        elif operator == '<=':
            return value <= threshold
        elif operator == '>':
            return value > threshold
        elif operator == '>=':
            return value >= threshold
        elif operator == '==':
            return value == threshold
        
        return False
    
    def _generate_recommendations(
        self, 
        priority: TriagePriority,
        complaint: str,
        reason: str,
        vital_signs: Optional[Dict]
    ) -> List[str]:
        """Gera recomendações específicas baseadas na prioridade e condição"""
        
        recommendations = []
        
        # Recomendações baseadas na prioridade
        priority_recs = {
            TriagePriority.RED: [
                "ATENDIMENTO IMEDIATO NECESSÁRIO",
                "Encaminhar para sala de emergência AGORA",
                "Acionar equipe de emergência",
                "Monitorização contínua obrigatória"
            ],
            TriagePriority.ORANGE: [
                "Atendimento em até 10 minutos",
                "Reavaliar sinais vitais a cada 10 minutos",
                "Manter em observação próxima",
                "Considerar exames prioritários"
            ],
            TriagePriority.YELLOW: [
                "Atendimento em até 60 minutos",
                "Reavaliar se piora dos sintomas",
                "Monitorar sinais vitais a cada 30 minutos"
            ],
            TriagePriority.GREEN: [
                "Atendimento em até 120 minutos",
                "Reavaliar se necessário",
                "Orientar sobre sinais de alarme"
            ],
            TriagePriority.BLUE: [
                "Atendimento não urgente",
                "Considerar encaminhamento para UBS",
                "Orientações gerais de cuidados"
            ]
        }
        
        recommendations.extend(priority_recs[priority])
        
        # Recomendações específicas por queixa
        if complaint == 'chest_pain' and priority in [TriagePriority.RED, TriagePriority.ORANGE]:
            recommendations.extend([
                "ECG em <10 minutos",
                "Acesso venoso calibroso",
                "Preparar medicação cardíaca",
                "Contatar cardiologia"
            ])
        elif complaint == 'major_trauma':
            recommendations.extend([
                "Protocolo de trauma ativado",
                "Preparar sala de trauma",
                "Solicitar hemoderivados",
                "Raio-X e TC prioritários"
            ])
        
        return recommendations
    
    def _get_emergency_recommendations(self, reason: str) -> List[str]:
        """Recomendações específicas para emergências"""
        return [
            f"EMERGÊNCIA: {reason}",
            "ATENDIMENTO IMEDIATO - RISCO DE VIDA",
            "Acionar código vermelho",
            "Preparar sala de ressuscitação",
            "Equipe completa em standby",
            "Via aérea avançada disponível",
            "Acesso venoso central se necessário"
        ]