# apps/core/management/commands/seed_data.py
"""
Comando para popular banco com dados iniciais de desenvolvimento
Cria unidades de saúde, especialidades e plantões de exemplo
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.facilities.models import Facility, MedicalSpecialty, MedicalShift
from apps.core.models import User
import random
from datetime import timedelta, time
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Popula banco com dados iniciais para desenvolvimento'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando seed do banco de dados...')
        
        # 1. Criar especialidades
        self.create_specialties()
        
        # 2. Criar unidades de saúde
        self.create_facilities()
        
        # 3. Criar usuários médicos
        self.create_medical_staff()
        
        # 4. Criar plantões
        self.create_shifts()
        
        self.stdout.write(self.style.SUCCESS('✓ Seed concluído com sucesso!'))

    def create_specialties(self):
        """Cria especialidades médicas padrão"""
        self.stdout.write('Criando especialidades médicas...')
        
        specialties = [
            ('CLINICA_GERAL', 'Clínica Geral', 'Atendimento geral e preventivo'),
            ('CARDIOLOGIA', 'Cardiologia', 'Doenças do coração e sistema circulatório'),
            ('ORTOPEDIA', 'Ortopedia', 'Ossos, músculos e articulações'),
            ('PEDIATRIA', 'Pediatria', 'Saúde infantil e do adolescente'),
            ('GINECOLOGIA', 'Ginecologia', 'Saúde da mulher'),
            ('OBSTETRICIA', 'Obstetrícia', 'Gravidez e parto'),
            ('NEUROLOGIA', 'Neurologia', 'Sistema nervoso'),
            ('PSIQUIATRIA', 'Psiquiatria', 'Saúde mental'),
            ('EMERGENCIA', 'Medicina de Emergência', 'Atendimento de urgência e emergência'),
            ('DERMATOLOGIA', 'Dermatologia', 'Pele e anexos'),
            ('OFTALMOLOGIA', 'Oftalmologia', 'Olhos e visão'),
            ('OTORRINO', 'Otorrinolaringologia', 'Ouvido, nariz e garganta'),
            ('UROLOGIA', 'Urologia', 'Sistema urinário'),
            ('GASTRO', 'Gastroenterologia', 'Sistema digestivo'),
            ('PNEUMOLOGIA', 'Pneumologia', 'Sistema respiratório'),
            ('REUMATOLOGIA', 'Reumatologia', 'Doenças reumáticas'),
            ('ENDOCRINOLOGIA', 'Endocrinologia', 'Sistema endócrino e metabólico'),
            ('HEMATOLOGIA', 'Hematologia', 'Sangue e órgãos hematopoiéticos'),
            ('ONCOLOGIA', 'Oncologia', 'Tratamento do câncer'),
            ('CIRURGIA', 'Cirurgia Geral', 'Procedimentos cirúrgicos'),
            ('ANESTESIA', 'Anestesiologia', 'Anestesia e controle da dor'),
        ]
        
        for code, name, description in specialties:
            specialty, created = MedicalSpecialty.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': description}
            )
            if created:
                self.stdout.write(f'  ✓ {name}')
    
    def create_facilities(self):
        """Cria unidades de saúde em Montes Claros e região"""
        self.stdout.write('Criando unidades de saúde...')
        
        facilities_data = [
            # Hospitais
            {
                'name': 'Hospital Santa Casa de Montes Claros',
                'official_code': 'CNES001',
                'facility_type': 'HOSPITAL',
                'address': 'Praça Honorato Alves, 22 - Centro',
                'city': 'Montes Claros',
                'zip_code': '39400-103',
                'latitude': Decimal('-16.7215'),
                'longitude': Decimal('-43.8766'),
                'phone_primary': '(38) 3229-2000',
                'phone_emergency': '(38) 3229-2001',
                'total_beds': 350,
                'icu_beds': 40,
                'emergency_beds': 20,
                'is_24h': True,
                'resources': ['tomografia', 'ressonancia', 'hemodinamica', 'uti_adulto', 'uti_neo', 'centro_cirurgico', 'sala_vermelha'],
                'specialties': ['EMERGENCIA', 'CARDIOLOGIA', 'NEUROLOGIA', 'CIRURGIA', 'ORTOPEDIA', 'PEDIATRIA']
            },
            {
                'name': 'Hospital Universitário Clemente de Faria',
                'official_code': 'CNES002',
                'facility_type': 'HOSPITAL',
                'address': 'Av. Cula Mangabeira, 562 - Santo Expedito',
                'city': 'Montes Claros',
                'zip_code': '39401-001',
                'latitude': Decimal('-16.7340'),
                'longitude': Decimal('-43.8621'),
                'phone_primary': '(38) 3224-8000',
                'phone_emergency': '(38) 3224-8001',
                'total_beds': 200,
                'icu_beds': 25,
                'emergency_beds': 15,
                'is_24h': True,
                'resources': ['tomografia', 'ressonancia', 'uti_adulto', 'centro_cirurgico', 'sala_vermelha'],
                'specialties': ['EMERGENCIA', 'CLINICA_GERAL', 'PEDIATRIA', 'GINECOLOGIA', 'OBSTETRICIA']
            },
            {
                'name': 'Hospital Aroldo Tourinho',
                'official_code': 'CNES003',
                'facility_type': 'HOSPITAL',
                'address': 'Rua Engenheiro Antônio Álvares, 85 - Centro',
                'city': 'Montes Claros',
                'zip_code': '39400-112',
                'latitude': Decimal('-16.7190'),
                'longitude': Decimal('-43.8795'),
                'phone_primary': '(38) 3229-1000',
                'phone_emergency': '(38) 3229-1001',
                'total_beds': 180,
                'icu_beds': 20,
                'emergency_beds': 10,
                'is_24h': True,
                'resources': ['tomografia', 'uti_adulto', 'centro_cirurgico'],
                'specialties': ['EMERGENCIA', 'CLINICA_GERAL', 'CIRURGIA']
            },
            
            # UPAs
            {
                'name': 'UPA Major Prates',
                'official_code': 'CNES004',
                'facility_type': 'UPA',
                'address': 'Av. Deputado Esteves Rodrigues, 852 - Major Prates',
                'city': 'Montes Claros',
                'zip_code': '39403-215',
                'latitude': Decimal('-16.7056'),
                'longitude': Decimal('-43.8925'),
                'phone_primary': '(38) 3213-7000',
                'phone_emergency': '(38) 3213-7001',
                'emergency_beds': 10,
                'is_24h': True,
                'resources': ['raio_x', 'eletrocardiograma', 'laboratorio'],
                'specialties': ['EMERGENCIA', 'CLINICA_GERAL', 'PEDIATRIA']
            },
            {
                'name': 'UPA Santos Reis',
                'official_code': 'CNES005',
                'facility_type': 'UPA',
                'address': 'Rua Delmiro Gouveia, 300 - Santos Reis',
                'city': 'Montes Claros',
                'zip_code': '39400-500',
                'latitude': Decimal('-16.7421'),
                'longitude': Decimal('-43.8534'),
                'phone_primary': '(38) 3213-8000',
                'phone_emergency': '(38) 3213-8001',
                'emergency_beds': 10,
                'is_24h': True,
                'resources': ['raio_x', 'eletrocardiograma', 'laboratorio'],
                'specialties': ['EMERGENCIA', 'CLINICA_GERAL', 'PEDIATRIA']
            },
            {
                'name': 'UPA Independência',
                'official_code': 'CNES006',
                'facility_type': 'UPA',
                'address': 'Av. Mestra Fininha, 2050 - Independência',
                'city': 'Montes Claros',
                'zip_code': '39404-128',
                'latitude': Decimal('-16.6989'),
                'longitude': Decimal('-43.8412'),
                'phone_primary': '(38) 3213-9000',
                'phone_emergency': '(38) 3213-9001',
                'emergency_beds': 8,
                'is_24h': True,
                'resources': ['raio_x', 'eletrocardiograma', 'laboratorio'],
                'specialties': ['EMERGENCIA', 'CLINICA_GERAL']
            },
            
            # UBS (algumas principais)
            {
                'name': 'UBS Centro de Saúde Maracanã',
                'official_code': 'CNES007',
                'facility_type': 'UBS',
                'address': 'Rua Ipiranga, 280 - Maracanã',
                'city': 'Montes Claros',
                'zip_code': '39401-256',
                'latitude': Decimal('-16.7312'),
                'longitude': Decimal('-43.8445'),
                'phone_primary': '(38) 3213-5500',
                'is_24h': False,
                'opening_time': time(7, 0),
                'closing_time': time(17, 0),
                'resources': ['vacina', 'farmacia_basica', 'preventivo'],
                'specialties': ['CLINICA_GERAL', 'PEDIATRIA', 'GINECOLOGIA']
            },
            {
                'name': 'UBS Jardim São Luiz',
                'official_code': 'CNES008',
                'facility_type': 'UBS',
                'address': 'Rua C, 95 - Jardim São Luiz',
                'city': 'Montes Claros',
                'zip_code': '39401-445',
                'latitude': Decimal('-16.7089'),
                'longitude': Decimal('-43.8678'),
                'phone_primary': '(38) 3213-6600',
                'is_24h': False,
                'opening_time': time(7, 0),
                'closing_time': time(17, 0),
                'resources': ['vacina', 'farmacia_basica', 'preventivo'],
                'specialties': ['CLINICA_GERAL', 'PEDIATRIA']
            },
            {
                'name': 'UBS Vila Oliveira',
                'official_code': 'CNES009',
                'facility_type': 'UBS',
                'address': 'Rua Joaquim Costa, 150 - Vila Oliveira',
                'city': 'Montes Claros',
                'zip_code': '39400-678',
                'latitude': Decimal('-16.7456'),
                'longitude': Decimal('-43.8901'),
                'phone_primary': '(38) 3213-7700',
                'is_24h': False,
                'opening_time': time(7, 0),
                'closing_time': time(17, 0),
                'resources': ['vacina', 'farmacia_basica'],
                'specialties': ['CLINICA_GERAL']
            },
            
            # Pronto-Socorro
            {
                'name': 'Pronto Socorro Municipal Alpheu de Quadros',
                'official_code': 'CNES010',
                'facility_type': 'PS',
                'address': 'Av. Norival Guilherme Vieira, 195 - Ibituruna',
                'city': 'Montes Claros',
                'zip_code': '39401-289',
                'latitude': Decimal('-16.7234'),
                'longitude': Decimal('-43.8556'),
                'phone_primary': '(38) 3690-2200',
                'phone_emergency': '(38) 3690-2201',
                'emergency_beds': 25,
                'is_24h': True,
                'resources': ['raio_x', 'tomografia', 'laboratorio', 'centro_cirurgico', 'sala_vermelha'],
                'specialties': ['EMERGENCIA', 'CIRURGIA', 'ORTOPEDIA', 'NEUROLOGIA']
            }
        ]
        
        for data in facilities_data:
            facility, created = Facility.objects.get_or_create(
                official_code=data['official_code'],
                defaults=data
            )
            if created:
                # Define ocupação aleatória inicial
                facility.current_occupancy_percent = random.randint(30, 85)
                facility.average_wait_time_minutes = random.randint(20, 120)
                facility.save()
                self.stdout.write(f'  ✓ {facility.name}')
    
    def create_medical_staff(self):
        """Cria usuários médicos e enfermeiros de exemplo"""
        self.stdout.write('Criando equipe médica...')
        
        # Pega primeira facility como padrão
        default_facility = Facility.objects.first()
        
        if not default_facility:
            self.stdout.write(self.style.WARNING('  ! Nenhuma facility encontrada'))
            return
        
        # Admin
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@ondeatende.com',
                'first_name': 'Admin',
                'last_name': 'Sistema',
                'professional_id': 'ADM001',
                'role': 'ADMIN',
                'facility': default_facility,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write('  ✓ Admin criado')
        
        # Médicos
        doctors = [
            ('dr.carlos', 'Carlos', 'Silva', 'CRM-MG 12345'),
            ('dra.maria', 'Maria', 'Santos', 'CRM-MG 23456'),
            ('dr.joao', 'João', 'Oliveira', 'CRM-MG 34567'),
            ('dra.ana', 'Ana', 'Costa', 'CRM-MG 45678'),
            ('dr.pedro', 'Pedro', 'Ferreira', 'CRM-MG 56789'),
        ]
        
        for username, first_name, last_name, crm in doctors:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@ondeatende.com',
                    'first_name': first_name,
                    'last_name': last_name,
                    'professional_id': crm,
                    'role': 'DOCTOR',
                    'facility': default_facility,
                    'is_staff': True,
                }
            )
            if created:
                user.set_password('doctor123')
                user.save()
                self.stdout.write(f'  ✓ Dr(a). {first_name} {last_name}')
        
        # Enfermeiros de triagem
        nurses = [
            ('enf.lucia', 'Lucia', 'Almeida', 'COREN-MG 11111'),
            ('enf.paulo', 'Paulo', 'Souza', 'COREN-MG 22222'),
            ('enf.julia', 'Julia', 'Lima', 'COREN-MG 33333'),
        ]
        
        for username, first_name, last_name, coren in nurses:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@ondeatende.com',
                    'first_name': first_name,
                    'last_name': last_name,
                    'professional_id': coren,
                    'role': 'TRIAGE_NURSE',
                    'facility': default_facility,
                    'is_staff': True,
                }
            )
            if created:
                user.set_password('nurse123')
                user.save()
                self.stdout.write(f'  ✓ Enf. {first_name} {last_name}')
    
    def create_shifts(self):
        """Cria plantões médicos para os próximos 7 dias"""
        self.stdout.write('Criando plantões médicos...')
        
        facilities = Facility.objects.all()
        doctors = User.objects.filter(role='DOCTOR')
        specialties = MedicalSpecialty.objects.all()
        
        if not doctors.exists():
            self.stdout.write(self.style.WARNING('  ! Nenhum médico encontrado'))
            return
        
        today = timezone.now().date()
        
        # Para cada facility
        for facility in facilities:
            # Cria plantões para os próximos 7 dias
            for day_offset in range(7):
                shift_date = today + timedelta(days=day_offset)
                
                # Define quantos plantões baseado no tipo da unidade
                if facility.facility_type == 'HOSPITAL':
                    shifts_per_day = 8
                elif facility.facility_type in ['UPA', 'PS']:
                    shifts_per_day = 4
                else:  # UBS
                    shifts_per_day = 2
                
                # Cria plantões aleatórios
                for _ in range(shifts_per_day):
                    doctor = random.choice(doctors)
                    specialty = random.choice(specialties)
                    
                    # Define horários baseado no tipo
                    if facility.is_24h:
                        # Plantões 24h têm turnos
                        shift_choice = random.choice([
                            (time(7, 0), time(19, 0)),   # Diurno
                            (time(19, 0), time(7, 0)),   # Noturno
                            (time(7, 0), time(13, 0)),   # Manhã
                            (time(13, 0), time(19, 0)),  # Tarde
                        ])
                    else:
                        # Horário comercial
                        shift_choice = (time(8, 0), time(17, 0))
                    
                    shift, created = MedicalShift.objects.get_or_create(
                        facility=facility,
                        doctor=doctor,
                        shift_date=shift_date,
                        start_time=shift_choice[0],
                        defaults={
                            'specialty': specialty,
                            'end_time': shift_choice[1],
                            'max_appointments': random.randint(15, 30),
                            'status': 'SCHEDULED' if day_offset > 0 else 'ACTIVE',
                        }
                    )
                    
                    if created and day_offset == 0:
                        # Simula alguns atendimentos para hoje
                        shift.current_appointments = random.randint(0, 10)
                        shift.save()
        
        self.stdout.write(f'  ✓ Plantões criados para {facilities.count()} unidades')