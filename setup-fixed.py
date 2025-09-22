#!/usr/bin/env python3
"""
setup-fixed.py - Script de configuração inicial do OndeAtende (CORRIGIDO)
Versão com melhor tratamento de erros e debug
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
        os.system('color')
    
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header():
    """Exibe o cabeçalho do setup"""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("=" * 50)
    print("    🏥 OndeAtende - Setup Inicial (v2.0)")
    print(f"    Sistema: {platform.system()} {platform.release()}")
    print(f"    Python: {sys.version.split()[0]}")
    print(f"    Diretório: {os.getcwd()}")
    print("=" * 50)
    print(f"{Colors.RESET}\n")


def check_command(command):
    """Verifica se um comando está instalado"""
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(['where', command], capture_output=True, text=True, shell=True)
        else:
            result = subprocess.run(['which', command], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"{Colors.GREEN}✓ {command} instalado{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}❌ {command} não encontrado{Colors.RESET}")
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ Erro ao verificar {command}: {e}{Colors.RESET}")
        return False


def check_dependencies():
    """Verifica todas as dependências necessárias"""
    print(f"{Colors.YELLOW}📋 Verificando dependências...{Colors.RESET}")
    
    required = {
        'docker': 'https://www.docker.com/products/docker-desktop/',
        'python': 'https://www.python.org/downloads/',
        'npm': 'https://nodejs.org/',
    }
    
    if platform.system() == 'Windows':
        required['docker-compose'] = 'Incluído no Docker Desktop'
    
    all_installed = True
    missing = []
    
    for cmd, url in required.items():
        if cmd == 'python':
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
    
    print(f"{Colors.GREEN}✅ Todas as dependências encontradas{Colors.RESET}")
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
        print("  Certifique-se de que está executando o script na raiz do projeto")
        return False
    
    try:
        print("  Copiando .env.example para .env...")
        shutil.copy(env_example_path, env_path)
        
        print("  Gerando SECRET_KEY...")
        secret_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(50))
        
        print("  Gerando ENCRYPTION_KEY...")
        try:
            from cryptography.fernet import Fernet
            encryption_key = Fernet.generate_key().decode()
        except ImportError:
            print(f"  {Colors.YELLOW}⚠ cryptography não instalado, usando token simples{Colors.RESET}")
            encryption_key = secrets.token_urlsafe(32)
        
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace('your-secret-key-here-change-in-production', secret_key)
        content = content.replace('generate-a-32-byte-key-and-base64-encode-it', encryption_key)
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"{Colors.GREEN}✓ Arquivo .env criado com sucesso{Colors.RESET}")
        return True
        
    except Exception as e:
        print(f"{Colors.RED}❌ Erro ao criar .env: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return False


def create_directories():
    """Cria os diretórios necessários"""
    print(f"\n{Colors.YELLOW}📁 Criando diretórios...{Colors.RESET}")
    
    directories = [
        'backend/logs',
        'backend/media',
        'backend/staticfiles',
        'backend/apps',
        'backend/apps/core',
        'backend/apps/core/management',
        'backend/apps/core/management/commands',
    ]
    
    created = 0
    existed = 0
    failed = 0
    
    for directory in directories:
        try:
            dir_path = Path(directory)
            if dir_path.exists():
                print(f"  ⚪ {directory} (já existe)")
                existed += 1
            else:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"  {Colors.GREEN}✓ {directory} (criado){Colors.RESET}")
                created += 1
        except Exception as e:
            print(f"  {Colors.RED}❌ Falha ao criar {directory}: {e}{Colors.RESET}")
            failed += 1
    
    print(f"\n  Resumo: {created} criados, {existed} já existiam, {failed} falharam")
    
    if failed > 0:
        print(f"{Colors.RED}❌ Alguns diretórios não puderam ser criados{Colors.RESET}")
        return False
    
    print(f"{Colors.GREEN}✓ Todos os diretórios prontos{Colors.RESET}")
    return True


def run_command(command, cwd=None, shell=False, timeout=30):
    """Executa um comando e retorna o resultado"""
    try:
        if platform.system() == 'Windows' and not isinstance(command, list):
            shell = True
        
        print(f"  {Colors.MAGENTA}$ {command if isinstance(command, str) else ' '.join(str(c) for c in command)}{Colors.RESET}")
        
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode != 0 and result.stderr:
            print(f"  {Colors.YELLOW}⚠ Stderr: {result.stderr[:200]}{Colors.RESET}")
        
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print(f"  {Colors.RED}❌ Comando demorou muito (timeout: {timeout}s){Colors.RESET}")
        return False, '', 'Timeout'
    except Exception as e:
        print(f"  {Colors.RED}❌ Erro ao executar comando: {e}{Colors.RESET}")
        return False, '', str(e)


def setup_python_env():
    """Configura o ambiente Python"""
    print(f"\n{Colors.YELLOW}🐍 Configurando ambiente Python...{Colors.RESET}")
    
    backend_path = Path('backend')
    if not backend_path.exists():
        print(f"{Colors.RED}❌ Diretório 'backend' não encontrado{Colors.RESET}")
        return False
    
    venv_path = backend_path / 'venv'
    requirements_path = backend_path / 'requirements.txt'
    
    if not requirements_path.exists():
        print(f"{Colors.RED}❌ Arquivo requirements.txt não encontrado{Colors.RESET}")
        return False
    
    python_cmd = 'python' if shutil.which('python') else 'python3'
    
    # Criar virtual environment
    if not venv_path.exists():
        print("  Criando virtual environment...")
        success, out, err = run_command([python_cmd, '-m', 'venv', 'venv'], cwd=backend_path)
        if not success:
            print(f"{Colors.RED}❌ Erro ao criar virtual environment{Colors.RESET}")
            if err:
                print(f"  Detalhes: {err}")
            return False
    else:
        print(f"  {Colors.GREEN}✓ Virtual environment já existe{Colors.RESET}")
    
    # Determinar caminhos baseado no OS
    if platform.system() == 'Windows':
        pip_path = venv_path / 'Scripts' / 'pip.exe'
        python_venv = venv_path / 'Scripts' / 'python.exe'
    else:
        pip_path = venv_path / 'bin' / 'pip'
        python_venv = venv_path / 'bin' / 'python'
    
    if not pip_path.exists():
        print(f"{Colors.RED}❌ pip não encontrado no venv: {pip_path}{Colors.RESET}")
        return False
    
    # Upgrade pip
    print("  Atualizando pip...")
    run_command([str(python_venv), '-m', 'pip', 'install', '--upgrade', 'pip'], timeout=60)
    
    # Instalar requirements
    print("  Instalando dependências Python (pode demorar alguns minutos)...")
    success, out, err = run_command(
        [str(pip_path), 'install', '-r', 'requirements.txt'],
        cwd=backend_path,
        timeout=300  # 5 minutos
    )
    
    if success:
        print(f"{Colors.GREEN}✓ Dependências Python instaladas{Colors.RESET}")
        return True
    else:
        print(f"{Colors.RED}❌ Erro ao instalar dependências Python{Colors.RESET}")
        if err:
            print(f"  Detalhes: {err[:500]}")
        return False


def setup_node_env():
    """Configura o ambiente Node.js"""
    print(f"\n{Colors.YELLOW}📦 Configurando ambiente Node.js...{Colors.RESET}")
    
    frontend_path = Path('frontend')
    if not frontend_path.exists():
        print(f"{Colors.RED}❌ Diretório 'frontend' não encontrado{Colors.RESET}")
        return False
    
    package_json = frontend_path / 'package.json'
    if not package_json.exists():
        print(f"{Colors.RED}❌ Arquivo package.json não encontrado{Colors.RESET}")
        return False
    
    node_modules = frontend_path / 'node_modules'
    
    if not node_modules.exists():
        print("  Instalando dependências Node (pode demorar alguns minutos)...")
        success, out, err = run_command('npm install', cwd=frontend_path, shell=True, timeout=300)
        
        if success:
            print(f"{Colors.GREEN}✓ Dependências Node instaladas{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}❌ Erro ao instalar dependências Node{Colors.RESET}")
            if err:
                print(f"  Detalhes: {err[:500]}")
            return False
    else:
        print(f"{Colors.GREEN}✓ Dependências Node já instaladas{Colors.RESET}")
        return True


def start_docker_services():
    """Inicia os serviços Docker necessários"""
    print(f"\n{Colors.YELLOW}🐳 Iniciando serviços Docker...{Colors.RESET}")
    
    # Verificar se Docker está rodando
    print("  Verificando Docker...")
    success, out, err = run_command('docker info', shell=True, timeout=10)
    if not success:
        print(f"{Colors.RED}❌ Docker não está rodando{Colors.RESET}")
        print(f"  {Colors.YELLOW}Por favor, inicie o Docker Desktop e tente novamente{Colors.RESET}")
        return False
    
    # Verificar docker-compose.yml
    if not Path('docker-compose.yml').exists() and not Path('docker-compose.yaml').exists():
        print(f"{Colors.RED}❌ Arquivo docker-compose.yml não encontrado{Colors.RESET}")
        return False
    
    # Iniciar containers
    print("  Iniciando banco de dados e Redis...")
    success, out, err = run_command('docker-compose up -d db redis', shell=True, timeout=60)
    
    if success:
        print(f"{Colors.GREEN}✓ Serviços Docker iniciados{Colors.RESET}")
        print("  Aguardando banco de dados inicializar (10 segundos)...")
        time.sleep(10)
        return True
    else:
        print(f"{Colors.RED}❌ Erro ao iniciar serviços Docker{Colors.RESET}")
        if err:
            print(f"  Detalhes: {err[:500]}")
        return False


def run_migrations():
    """Executa as migrações do Django"""
    print(f"\n{Colors.YELLOW}🔄 Executando migrações do banco de dados...{Colors.RESET}")
    
    backend_path = Path('backend')
    manage_py = backend_path / 'manage.py'
    
    if not manage_py.exists():
        print(f"{Colors.RED}❌ manage.py não encontrado{Colors.RESET}")
        return False
    
    if platform.system() == 'Windows':
        python_venv = backend_path / 'venv' / 'Scripts' / 'python.exe'
    else:
        python_venv = backend_path / 'venv' / 'bin' / 'python'
    
    if not python_venv.exists():
        print(f"{Colors.RED}❌ Python do venv não encontrado: {python_venv}{Colors.RESET}")
        return False
    
    # makemigrations
    print("  Criando migrações...")
    success, out, err = run_command(
        [str(python_venv), 'manage.py', 'makemigrations'],
        cwd=backend_path,
        timeout=30
    )
    
    # migrate
    print("  Aplicando migrações...")
    success, out, err = run_command(
        [str(python_venv), 'manage.py', 'migrate'],
        cwd=backend_path,
        timeout=60
    )
    
    if success:
        print(f"{Colors.GREEN}✓ Migrações aplicadas com sucesso{Colors.RESET}")
        return True
    else:
        print(f"{Colors.RED}❌ Erro ao aplicar migrações{Colors.RESET}")
        if err:
            print(f"  Detalhes: {err[:500]}")
        return False


def seed_database():
    """Popula o banco com dados iniciais"""
    print(f"\n{Colors.YELLOW}🌱 Populando banco de dados...{Colors.RESET}")
    
    backend_path = Path('backend')
    
    if platform.system() == 'Windows':
        python_venv = backend_path / 'venv' / 'Scripts' / 'python.exe'
    else:
        python_venv = backend_path / 'venv' / 'bin' / 'python'
    
    print("  Executando comando seed_data...")
    success, out, err = run_command(
        [str(python_venv), 'manage.py', 'seed_data'],
        cwd=backend_path,
        timeout=60
    )
    
    if success:
        print(f"{Colors.GREEN}✓ Dados iniciais criados{Colors.RESET}")
    else:
        # O comando pode não existir, o que é OK
        if "Unknown command" in (err or '') or "No command" in (err or ''):
            print(f"{Colors.YELLOW}⚠ Comando seed_data não encontrado (normal se for primeira execução){Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}⚠ Possível erro ao popular dados{Colors.RESET}")
    
    return True


def create_superuser():
    """Cria o superusuário admin"""
    print(f"\n{Colors.YELLOW}👤 Criando superusuário admin...{Colors.RESET}")
    
    backend_path = Path('backend')
    
    if platform.system() == 'Windows':
        python_venv = backend_path / 'venv' / 'Scripts' / 'python.exe'
    else:
        python_venv = backend_path / 'venv' / 'bin' / 'python'
    
    create_user_script = """
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@ondeatende.com',
            password='admin123'
        )
        print('Superusuário admin criado com sucesso!')
    else:
        print('Superusuário admin já existe!')
except Exception as e:
    print(f'Erro ao criar superusuário: {e}')
"""
    
    print("  Verificando/criando superusuário...")
    success, out, err = run_command(
        [str(python_venv), 'manage.py', 'shell', '-c', create_user_script],
        cwd=backend_path,
        timeout=30
    )
    
    if out:
        print(f"  {out.strip()}")
    
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
        print(f"{Colors.CYAN}   Execute o arquivo batch:{Colors.RESET}")
        print("   .\\run-dev.bat")
        print("\n   Ou manualmente em dois terminais:")
        print("   Terminal 1 - Backend:")
        print("   cd backend")
        print("   .\\venv\\Scripts\\activate")
        print("   python manage.py runserver\n")
        print("   Terminal 2 - Frontend:")
        print("   cd frontend")
        print("   npm run dev")
    else:
        print(f"{Colors.CYAN}   Execute:{Colors.RESET}")
        print("   make dev")
    
    print(f"\n{Colors.GREEN}📱 O sistema estará disponível em:{Colors.RESET}")
    print("   Frontend: http://localhost:5173")
    print("   Backend:  http://localhost:8000")
    print("   Admin:    http://localhost:8000/admin\n")


def main():
    """Função principal do setup"""
    print_header()
    
    # Verificar diretório
    if not Path('backend').exists() or not Path('frontend').exists():
        print(f"{Colors.RED}❌ Execute este script na raiz do projeto OndeAtende{Colors.RESET}")
        print(f"  Diretório atual: {os.getcwd()}")
        print(f"  Esperado: diretórios 'backend' e 'frontend' presentes")
        sys.exit(1)
    
    # Lista de passos com seus nomes e funções
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
    
    total_steps = len(steps)
    
    for i, (step_name, step_func) in enumerate(steps, 1):
        print(f"\n{Colors.BOLD}[{i}/{total_steps}] {step_name}...{Colors.RESET}")
        
        if not step_func():
            print(f"\n{Colors.RED}❌ Setup falhou no passo: {step_name}{Colors.RESET}")
            print(f"{Colors.YELLOW}💡 Dicas para resolver:{Colors.RESET}")
            
            if "dependências" in step_name.lower():
                print("  - Instale as ferramentas necessárias listadas acima")
            elif "docker" in step_name.lower():
                print("  - Verifique se o Docker Desktop está rodando")
                print("  - No Windows, o ícone do Docker deve estar verde na bandeja")
            elif "python" in step_name.lower():
                print("  - Verifique se Python 3.8+ está instalado")
                print("  - Tente: python --version ou python3 --version")
            elif "node" in step_name.lower():
                print("  - Verifique se Node.js está instalado")
                print("  - Tente: npm --version")
            elif "migrações" in step_name.lower():
                print("  - Verifique se o banco de dados está rodando")
                print("  - Tente: docker ps")
            
            print(f"\n{Colors.CYAN}Após resolver o problema, execute o script novamente{Colors.RESET}")
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
        import traceback
        traceback.print_exc()
        sys.exit(1)