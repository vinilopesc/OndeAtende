#!/usr/bin/env python3
"""
setup.py - Script de configuração inicial do OndeAtende
Funciona em Windows, Mac e Linux
"""

import os
import sys
import subprocess
import platform
import shutil
import time
import secrets
import string
from pathlib import Path


class Colors:
    """Cores para output no terminal"""
    if platform.system() == 'Windows':
        # Windows pode não suportar cores ANSI em algumas versões
        os.system('color')
    
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header():
    """Exibe o cabeçalho do setup"""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("=" * 50)
    print("    🏥 OndeAtende - Setup Inicial")
    print(f"    Sistema: {platform.system()} {platform.release()}")
    print("=" * 50)
    print(f"{Colors.RESET}\n")


def check_command(command):
    """Verifica se um comando está instalado"""
    try:
        if platform.system() == 'Windows':
            # Windows usa 'where'
            result = subprocess.run(
                ['where', command],
                capture_output=True,
                text=True,
                shell=True
            )
        else:
            # Unix usa 'which'
            result = subprocess.run(
                ['which', command],
                capture_output=True,
                text=True
            )
        
        if result.returncode == 0:
            print(f"{Colors.GREEN}✓ {command} instalado{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}❌ {command} não encontrado{Colors.RESET}")
            return False
    except Exception:
        print(f"{Colors.RED}❌ {command} não encontrado{Colors.RESET}")
        return False


def check_dependencies():
    """Verifica todas as dependências necessárias"""
    print(f"{Colors.YELLOW}📋 Verificando dependências...{Colors.RESET}")
    
    required = {
        'docker': 'https://www.docker.com/products/docker-desktop/',
        'python': 'https://www.python.org/downloads/',
        'npm': 'https://nodejs.org/',
    }
    
    # Para Windows, verificar docker-compose separadamente
    if platform.system() == 'Windows':
        required['docker-compose'] = 'Incluído no Docker Desktop'
    
    all_installed = True
    missing = []
    
    for cmd, url in required.items():
        if cmd == 'python':
            # Python pode estar como python3 em alguns sistemas
            if not check_command('python') and not check_command('python3'):
                all_installed = False
                missing.append((cmd, url))
        else:
            if not check_command(cmd):
                all_installed = False
                missing.append((cmd, url))
    
    if not all_installed:
        print(f"\n{Colors.YELLOW}⚠️  Instale as dependências faltantes:{Colors.RESET}")
        for cmd, url in missing:
            print(f"  {cmd}: {Colors.CYAN}{url}{Colors.RESET}")
        return False
    
    return True


def create_env_file():
    """Cria o arquivo .env com chaves geradas"""
    print(f"\n{Colors.YELLOW}🔧 Configurando arquivo .env...{Colors.RESET}")
    
    env_path = Path('.env')
    env_example_path = Path('.env.example')
    
    if env_path.exists():
        print(f"{Colors.YELLOW}⚠ Arquivo .env já existe{Colors.RESET}")
        return True
    
    if not env_example_path.exists():
        print(f"{Colors.RED}❌ Arquivo .env.example não encontrado!{Colors.RESET}")
        return False
    
    try:
        # Copiar .env.example para .env
        shutil.copy(env_example_path, env_path)
        
        # Gerar SECRET_KEY
        secret_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(50))
        
        # Gerar ENCRYPTION_KEY
        try:
            from cryptography.fernet import Fernet
            encryption_key = Fernet.generate_key().decode()
        except ImportError:
            # Se cryptography não estiver instalado, gerar uma chave aleatória
            encryption_key = secrets.token_urlsafe(32)
        
        # Ler conteúdo do arquivo
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Substituir valores
        content = content.replace('your-secret-key-here-change-in-production', secret_key)
        content = content.replace('generate-a-32-byte-key-and-base64-encode-it', encryption_key)
        
        # Escrever de volta
        with open(env_path, 'w') as f:
            f.write(content)
        
        print(f"{Colors.GREEN}✓ Arquivo .env criado com sucesso{Colors.RESET}")
        return True
        
    except Exception as e:
        print(f"{Colors.RED}❌ Erro ao criar .env: {e}{Colors.RESET}")
        return False


def create_directories():
    """Cria os diretórios necessários"""
    print(f"\n{Colors.YELLOW}📁 Criando diretórios...{Colors.RESET}")
    
    directories = [
        'backend/logs',
        'backend/media',
        'backend/staticfiles',
        'backend/apps/core/management/commands',
    ]
    
    try:
        for directory in directories:
            dir_path = Path(directory)
            dir_path.mkdir(parents=True, exist_ok=True)
            if dir_path.exists():
                print(f"  ✓ {directory}")
            else:
                print(f"  ❌ Falha ao criar {directory}")
                return False
        
        print(f"{Colors.GREEN}✓ Todos os diretórios criados{Colors.RESET}")
        return True  # IMPORTANTE: Estava faltando este return!
    except Exception as e:
        print(f"{Colors.RED}❌ Erro ao criar diretórios: {e}{Colors.RESET}")
        return False


def run_command(command, cwd=None, shell=False):
    """Executa um comando e retorna o resultado"""
    try:
        # No Windows, sempre usar shell=True para comandos complexos
        if platform.system() == 'Windows' and not isinstance(command, list):
            shell = True
        
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=shell,
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, '', str(e)


def setup_python_env():
    """Configura o ambiente Python"""
    print(f"\n{Colors.YELLOW}🐍 Configurando ambiente Python...{Colors.RESET}")
    
    backend_path = Path('backend')
    venv_path = backend_path / 'venv'
    
    # Determinar comando Python
    python_cmd = 'python' if shutil.which('python') else 'python3'
    
    # Criar virtual environment se não existir
    if not venv_path.exists():
        print("Criando virtual environment...")
        success, _, _ = run_command(
            [python_cmd, '-m', 'venv', 'venv'],
            cwd=backend_path
        )
        if not success:
            print(f"{Colors.RED}❌ Erro ao criar virtual environment{Colors.RESET}")
            return False
    
    # Determinar pip path baseado no OS
    if platform.system() == 'Windows':
        pip_path = venv_path / 'Scripts' / 'pip.exe'
        python_venv = venv_path / 'Scripts' / 'python.exe'
    else:
        pip_path = venv_path / 'bin' / 'pip'
        python_venv = venv_path / 'bin' / 'python'
    
    # Upgrade pip
    print("Atualizando pip...")
    run_command([str(python_venv), '-m', 'pip', 'install', '--upgrade', 'pip'])
    
    # Instalar requirements
    print("Instalando dependências Python...")
    success, _, _ = run_command(
        [str(pip_path), 'install', '-r', 'requirements.txt'],
        cwd=backend_path
    )
    
    if success:
        print(f"{Colors.GREEN}✓ Dependências Python instaladas{Colors.RESET}")
        return True
    else:
        print(f"{Colors.RED}❌ Erro ao instalar dependências Python{Colors.RESET}")
        return False


def setup_node_env():
    """Configura o ambiente Node.js"""
    print(f"\n{Colors.YELLOW}📦 Configurando ambiente Node.js...{Colors.RESET}")
    
    frontend_path = Path('frontend')
    
    if not (frontend_path / 'node_modules').exists():
        print("Instalando dependências Node...")
        success, _, _ = run_command('npm install', cwd=frontend_path, shell=True)
        
        if success:
            print(f"{Colors.GREEN}✓ Dependências Node instaladas{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}❌ Erro ao instalar dependências Node{Colors.RESET}")
            return False
    else:
        print(f"{Colors.GREEN}✓ Dependências Node já instaladas{Colors.RESET}")
        return True


def start_docker_services():
    """Inicia os serviços Docker necessários"""
    print(f"\n{Colors.YELLOW}🐳 Iniciando serviços Docker...{Colors.RESET}")
    
    # Verificar se Docker está rodando
    success, _, _ = run_command('docker info', shell=True)
    if not success:
        print(f"{Colors.RED}❌ Docker não está rodando. Por favor inicie o Docker Desktop{Colors.RESET}")
        return False
    
    # Iniciar containers
    print("Iniciando banco de dados e Redis...")
    success, _, _ = run_command('docker-compose up -d db redis', shell=True)
    
    if success:
        print(f"{Colors.GREEN}✓ Serviços Docker iniciados{Colors.RESET}")
        print("Aguardando banco de dados inicializar (10 segundos)...")
        time.sleep(10)
        return True
    else:
        print(f"{Colors.RED}❌ Erro ao iniciar serviços Docker{Colors.RESET}")
        return False


def run_migrations():
    """Executa as migrações do Django"""
    print(f"\n{Colors.YELLOW}🔄 Executando migrações...{Colors.RESET}")
    
    backend_path = Path('backend')
    
    # Determinar python path
    if platform.system() == 'Windows':
        python_venv = backend_path / 'venv' / 'Scripts' / 'python.exe'
    else:
        python_venv = backend_path / 'venv' / 'bin' / 'python'
    
    # Executar makemigrations
    print("Criando migrações...")
    run_command([str(python_venv), 'manage.py', 'makemigrations'], cwd=backend_path)
    
    # Executar migrate
    print("Aplicando migrações...")
    success, _, _ = run_command([str(python_venv), 'manage.py', 'migrate'], cwd=backend_path)
    
    if success:
        print(f"{Colors.GREEN}✓ Migrações aplicadas{Colors.RESET}")
        return True
    else:
        print(f"{Colors.RED}❌ Erro ao aplicar migrações{Colors.RESET}")
        return False


def seed_database():
    """Popula o banco com dados iniciais"""
    print(f"\n{Colors.YELLOW}🌱 Populando banco de dados...{Colors.RESET}")
    
    backend_path = Path('backend')
    
    # Determinar python path
    if platform.system() == 'Windows':
        python_venv = backend_path / 'venv' / 'Scripts' / 'python.exe'
    else:
        python_venv = backend_path / 'venv' / 'bin' / 'python'
    
    # Executar seed_data
    success, _, _ = run_command([str(python_venv), 'manage.py', 'seed_data'], cwd=backend_path)
    
    if success:
        print(f"{Colors.GREEN}✓ Dados iniciais criados{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}⚠ Comando seed_data pode não existir ainda{Colors.RESET}")
    
    return True


def create_superuser():
    """Cria o superusuário admin"""
    print(f"\n{Colors.YELLOW}👤 Criando superusuário admin...{Colors.RESET}")
    
    backend_path = Path('backend')
    
    # Determinar python path
    if platform.system() == 'Windows':
        python_venv = backend_path / 'venv' / 'Scripts' / 'python.exe'
    else:
        python_venv = backend_path / 'venv' / 'bin' / 'python'
    
    # Script Python para criar superuser
    create_user_script = """
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    from apps.facilities.models import Facility
    facility = Facility.objects.first()
    if facility:
        User.objects.create_superuser(
            username='admin',
            email='admin@ondeatende.com',
            password='admin123',
            professional_id='ADM001',
            role='ADMIN',
            facility=facility
        )
        print('Superusuário criado com sucesso!')
    else:
        # Criar usuário sem facility
        User.objects.create_superuser(
            username='admin',
            email='admin@ondeatende.com',
            password='admin123'
        )
        print('Superusuário criado (sem facility)')
else:
    print('Superusuário já existe!')
"""
    
    # Executar script
    success, output, _ = run_command(
        [str(python_venv), 'manage.py', 'shell', '-c', create_user_script],
        cwd=backend_path
    )
    
    print(output)
    return True


def print_success():
    """Exibe mensagem de sucesso e instruções"""
    print(f"\n{Colors.GREEN}{'=' * 50}")
    print("✅ Setup concluído com sucesso!")
    print(f"{'=' * 50}{Colors.RESET}\n")
    
    print(f"{Colors.CYAN}📝 Credenciais de acesso:{Colors.RESET}")
    print("   Admin: admin / admin123")
    print("   Médico: dr.carlos / doctor123")
    print("   Enfermeiro: enf.lucia / nurse123\n")
    
    print(f"{Colors.YELLOW}🚀 Para iniciar o sistema:{Colors.RESET}\n")
    
    if platform.system() == 'Windows':
        print(f"{Colors.CYAN}   No Windows, execute:{Colors.RESET}")
        print("   .\\run-dev.bat")
        print("\n   Ou manualmente:")
        print("   # Terminal 1 - Backend:")
        print("   cd backend")
        print("   .\\venv\\Scripts\\activate")
        print("   python manage.py runserver\n")
        print("   # Terminal 2 - Frontend:")
        print("   cd frontend")
        print("   npm run dev")
    else:
        print(f"{Colors.CYAN}   No Linux/Mac, execute:{Colors.RESET}")
        print("   make dev")
        print("\n   Ou manualmente:")
        print("   # Terminal 1 - Backend:")
        print("   cd backend")
        print("   source venv/bin/activate")
        print("   python manage.py runserver\n")
        print("   # Terminal 2 - Frontend:")
        print("   cd frontend")
        print("   npm run dev")
    
    print(f"\n{Colors.GREEN}📱 O sistema estará disponível em:{Colors.RESET}")
    print("   Frontend: http://localhost:5173")
    print("   Backend:  http://localhost:8000")
    print("   Admin:    http://localhost:8000/admin\n")


def main():
    """Função principal do setup"""
    print_header()
    
    # Verificar se está no diretório correto
    if not Path('backend').exists() or not Path('frontend').exists():
        print(f"{Colors.RED}❌ Execute este script na raiz do projeto OndeAtende{Colors.RESET}")
        sys.exit(1)
    
    # Executar setup passo a passo
    steps = [
        ("Verificando dependências", check_dependencies),
        ("Criando arquivo .env", create_env_file),
        ("Criando diretórios", create_directories),
        ("Configurando Python", setup_python_env),
        ("Configurando Node.js", setup_node_env),
        ("Iniciando Docker", start_docker_services),
        ("Executando migrações", run_migrations),
        ("Populando banco", seed_database),
        ("Criando admin", create_superuser),
    ]
    
    for step_name, step_func in steps:
        if not step_func():
            print(f"\n{Colors.RED}❌ Setup falhou em: {step_name}{Colors.RESET}")
            print(f"{Colors.YELLOW}Corrija o erro e execute novamente{Colors.RESET}")
            sys.exit(1)
    
    # Sucesso!
    print_success()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Setup cancelado pelo usuário{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Erro inesperado: {e}{Colors.RESET}")
        sys.exit(1)