# 🏥 OndeAtende - Sistema de Triagem Manchester

Sistema inteligente de triagem médica e roteamento de pacientes usando o protocolo Manchester, desenvolvido para otimizar o atendimento no SUS.

![Status](https://img.shields.io/badge/status-MVP-green)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/django-5.0-green)
![React](https://img.shields.io/badge/react-18-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

## 📋 Funcionalidades

### Para Pacientes
- 🔍 **Busca por Especialidade**: Encontre unidades com a especialidade médica necessária
- 🚨 **Triagem Manchester**: Auto-triagem com protocolo internacional
- 📍 **Geolocalização**: Unidades mais próximas com menor tempo de espera
- ⏱️ **Tempo Real**: Informações atualizadas sobre plantões e ocupação

### Para Profissionais de Saúde
- 👩‍⚕️ **Dashboard de Triagem**: Interface completa para enfermeiros triadores
- 📊 **Gestão de Filas**: Visualização em tempo real por prioridade
- 📈 **Analytics**: Métricas de performance e qualidade
- 🔔 **WebSockets**: Notificações instantâneas de emergências

## 🚀 Quick Start

### Pré-requisitos
- Docker e Docker Compose
- Python 3.11+
- Node.js 20+
- PostgreSQL 14+

### Instalação Rápida

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/ondeatende.git
cd ondeatende

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# Inicie com Docker
make up

# Ou desenvolvimento local
make dev
```

O sistema estará disponível em:
- 🌐 Frontend: http://localhost:5173
- 🔧 Backend: http://localhost:8000
- 📊 Admin: http://localhost:8000/admin

### Credenciais Padrão
```
Admin: admin / admin123
Médico: dr.carlos / doctor123
Enfermeiro: enf.lucia / nurse123
```

## 🏗️ Arquitetura

### Stack Tecnológico

#### Backend
- **Django 5.0**: Framework principal
- **Django REST Framework**: APIs RESTful
- **PostgreSQL + PostGIS**: Banco de dados com suporte geoespacial
- **Redis**: Cache e filas
- **Celery**: Tarefas assíncronas
- **Channels**: WebSockets
- **Gunicorn**: Servidor WSGI

#### Frontend
- **React 18**: Interface reativa
- **TypeScript**: Type safety
- **Tailwind CSS**: Estilização
- **Vite**: Build tool
- **Socket.io**: Comunicação real-time

### Estrutura do Projeto

```
ondeatende/
├── backend/
│   ├── apps/
│   │   ├── core/          # Autenticação, permissões, auditoria
│   │   ├── facilities/    # Unidades de saúde e plantões
│   │   ├── triage/        # Sistema de triagem Manchester
│   │   └── analytics/     # Dashboards e relatórios
│   ├── config/            # Configurações Django
│   └── requirements.txt   # Dependências Python
├── frontend/
│   ├── src/
│   │   ├── components/    # Componentes React
│   │   ├── services/      # APIs e WebSockets
│   │   └── App.tsx        # Aplicação principal
│   └── package.json       # Dependências Node
├── docker-compose.yml     # Orquestração de containers
└── Makefile              # Comandos automatizados
```

## 📱 Fluxo de Uso

### Busca por Especialidade
1. Usuário seleciona especialidade desejada
2. Sistema busca unidades com plantões ativos
3. Calcula score baseado em: distância, ocupação, tipo de unidade
4. Retorna top 3 unidades recomendadas

### Triagem Manchester
1. Paciente descreve sintomas principais
2. Responde discriminadores específicos
3. Sistema calcula prioridade (RED → BLUE)
4. Recomenda unidades baseado na urgência
5. Fornece orientações e tempo estimado

## 🔧 Comandos Úteis

```bash
# Desenvolvimento
make dev          # Inicia ambiente local
make migrate      # Roda migrações
make seed         # Popula dados iniciais
make test         # Executa testes
make shell        # Shell Django

# Docker
make build        # Build das imagens
make up           # Sobe containers
make down         # Para containers
make logs         # Visualiza logs

# Produção
make deploy       # Deploy completo
make backup       # Backup do banco
```

## 📊 API Documentation

### Endpoints Principais

#### Públicos
- `GET /api/v1/facilities/` - Lista unidades de saúde
- `GET /api/v1/facilities/search/by_specialty/` - Busca por especialidade
- `POST /api/v1/triage/public/self_triage/` - Auto-triagem

#### Autenticados
- `POST /api/v1/auth/login/` - Login
- `GET /api/v1/triage/queue/` - Fila de triagem
- `POST /api/v1/triage/sessions/` - Nova sessão de triagem
- `GET /api/v1/analytics/dashboard/` - Dashboard

### WebSocket Events

```javascript
// Conectar
ws://localhost:8000/ws/triage/{facility_id}/

// Eventos
{
  "type": "queue_update",      // Atualização da fila
  "type": "emergency_alert",   // Alerta de emergência
  "type": "patient_called"      // Paciente chamado
}
```

## 🏥 Protocolo Manchester

### Níveis de Prioridade

| Cor | Prioridade | Tempo Alvo | Descrição |
|-----|------------|------------|-----------|
| 🔴 RED | Emergência | Imediato | Risco de vida iminente |
| 🟠 ORANGE | Muito Urgente | 10 min | Condição crítica |
| 🟡 YELLOW | Urgente | 60 min | Condição urgente |
| 🟢 GREEN | Pouco Urgente | 120 min | Condição menos urgente |
| 🔵 BLUE | Não Urgente | 240 min | Condição não urgente |

## 🔒 Segurança e Compliance

- **HIPAA Compliant**: Proteção de dados médicos
- **LGPD**: Conformidade com lei brasileira
- **Criptografia**: PHI criptografado (AES-256)
- **Auditoria**: Log completo de acessos
- **RBAC**: Controle de acesso baseado em roles

## 📈 Monitoramento

- **Healthcheck**: `/healthz`
- **Metrics**: `/metrics` (Prometheus)
- **Logs**: Estruturados em JSON
- **Sentry**: Tracking de erros

## 🧪 Testes

```bash
# Testes unitários
make test

# Coverage
make test-coverage

# E2E (em desenvolvimento)
cd frontend && npm run test:e2e
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Roadmap

- [x] MVP - Sistema básico de triagem
- [x] Busca por especialidade
- [x] WebSockets para real-time
- [ ] App Mobile (React Native)
- [ ] Integração com CNES
- [ ] ML para predição de tempo
- [ ] Integração com prontuário eletrônico
- [ ] PWA offline-first

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👥 Time

- **Vini** - Engenheiro de Dados & Co-fundador Vórtex
- Contribuidores são bem-vindos!

## 📞 Suporte

- 📧 Email: suporte@ondeatende.com
- 📱 WhatsApp: (38) 99999-9999
- 🐛 Issues: [GitHub Issues](https://github.com/seu-usuario/ondeatende/issues)

---

Desenvolvido com ❤️ para melhorar o atendimento no SUS