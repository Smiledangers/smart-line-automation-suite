# Smart LINE Bot + Dashboard + Automation Suite

## 🎯 Project Overview

A complete **multi-platform chatbot system** with unified messaging, AI services, and automation pipelines. Supports LINE, Telegram, WhatsApp, and Discord with a central dashboard for customer service management.

**Use cases:**
- Multi-platform customer service bot
- AI-powered automated responses
- Web widget for website chat
- Customer service handoff (AI ↔ Human)
- Third-party API integration
- Scheduled scraping jobs

## 🧩 System Architecture

### Core Components
1. **Unified Messaging** - One API, all platforms
2. **Multi-Platform Support** - LINE, Telegram, WhatsApp, Discord
3. **AI Service** - LangGraph + OpenAI/LLaMA
4. **Web Widget** - Embedded chat for websites
5. **Agent Dashboard** - Human-in-the-loop customer service
6. **Scraping Pipeline** - Celery-powered automation
7. **Webhook System** - External notifications
8. **API Keys** - Third-party access management

## 🚀 Quick Start

### Using Docker Compose

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your keys
# Required: LINE_CHANNEL_ACCESS_TOKEN, OPENAI_API_KEY, DATABASE_URL

# 3. Build and start
docker-compose up -d --build

# 4. Run migrations
docker-compose exec web alembic upgrade head

# 5. Create admin
docker-compose exec web python scripts/create_superuser.py

# 6. Access
# API Docs: http://localhost:8000/docs
# Health: http://localhost:8000/health
```

### Local Development

```bash
# 1. Create venv
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate

# 2. Install
pip install -r requirements/base.txt
pip install -r requirements/dev.txt

# 3. Setup
cp .env.example .env
python scripts/init_db.py
alembic upgrade head
python scripts/create_superuser.py

# 4. Run
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📁 Project Structure

```
demo_project/
├── app/
│   ├── api/v1/endpoints/   # API endpoints
│   ├── core/               # Config, database, security
│   ├── Models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/          # Business logic
│   ├── tasks/             # Celery tasks
│   ├── middleware/       # Custom middleware
│   └── main.py            # FastAPI entry
├── alembic/versions/      # Migrations
├── requirements/          # Dependencies
├── scripts/               # Helper scripts
├── deploy/                # Deployment configs
├── tests/                 # Tests
├── docs/                  # Documentation
├── .github/workflows/    # CI/CD
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── Makefile
```

## ⭐ Features

### Multi-Platform Messaging
| Platform | Webhook | Send | Status |
|----------|--------|------|-------|
| LINE | ✅ | ✅ | ✅ |
| Telegram | ✅ | ✅ | ✅ |
| WhatsApp | ✅ | ✅ | ✅ |
| Discord | ✅ | ✅ | ✅ |

### Bot Capabilities
- Message receiving/replying
- User management
- Rich menus & buttons
- Quick replies
- Flex messages
- WebSocket chat widget

### Customer Service
- AI ↔ Human handoff
- Conversation assignment
- Pending queue management
- Agent dashboard API
- Real-time stats

### Third-Party API
- API Key management
- Permission control
- Rate limiting
- Usage tracking

### Webhooks
- Event triggers (message sent/received, conversation start/end)
- External notifications
- Signature verification

### AI Service
- LangGraph conversations
- Multi-model support (GPT-4, GPT-3.5, local LLaMA)
- Circuit breaker protection
- Async processing

### Scraping Pipeline
- Job scheduling (Celery beat)
- Multi-website support
- Automatic retry
- Status tracking

### Security
- JWT authentication
- Password hashing (bcrypt)
- Role-based access control
- CORS configuration
- Rate limiting
- Security headers

### Infrastructure
- PostgreSQL + Redis
- Docker/K8s/Helm/Terraform
- GitHub Actions CI/CD
- Prometheus metrics
- Health checks
- Database migrations

## 🔧 Configuration

### Required Keys
```bash
# Platform tokens
LINE_CHANNEL_ACCESS_TOKEN=xxx
LINE_CHANNEL_SECRET=xxx
TELEGRAM_BOT_TOKEN=xxx
WHATSAPP_PHONE_NUMBER_ID=xxx
WHATSAPP_ACCESS_TOKEN=xxx
DISCORD_BOT_TOKEN=xxx

# AI
OPENAI_API_KEY=xxx

# Database
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...

# Security
SECRET_KEY=your-secret-key
```

### Optional Keys
```bash
# Email notifications
SMTP_HOST=smtp.gmail.com
SMTP_USER=xxx
SMTP_PASSWORD=xxx

# Monitoring
SENTRY_DNS=xxx
PROMETHEUS_PORT=9090
```

## 📡 API Endpoints

### Core
| Endpoint | Description |
|----------|-------------|
| `/api/v1/line/webhook` | LINE webhook |
| `/api/v1/telegram/webhook` | Telegram webhook |
| `/api/v1/whatsapp/webhook` | WhatsApp webhook |
| `/api/v1/discord/webhook` | Discord webhook |
| `/api/v1/ai/chat` | AI chat |
| `/api/v1/widget/ws/{session_id}` | WebSocket chat |

### Management
| Endpoint | Description |
|----------|-------------|
| `/api/v1/dashboard/users` | User management |
| `/api/v1/api-keys` | API key CRUD |
| `/api/v1/webhooks` | Webhook CRUD |
| `/api/v1/agent/conversations` | Agent dashboard |
| `/api/v1/agent/handoff` | AI ↔ Human transfer |
| `/api/v1/scraping/jobs` | Scraping jobs |

## 🧪 Testing

```bash
# All tests
pytest

# By category
pytest tests/unit/
pytest tests/integration/

# With coverage
pytest --cov=app --cov-report=term-missing
```

## 📦 Deployment

| Method | Command |
|--------|---------|
| Docker | `docker-compose up -d` |
| Production | `docker-compose -f docker-compose.prod.yml up -d` |
| K8s | `kubectl apply -f deploy/k8s/` |
| Helm | `helm install demo-bot ./deploy/helm/demo-bot/` |

## 🔨 Makefile Commands

```bash
make install         # Install dependencies
make test            # Run tests
make lint            # Run linters
make format         # Format code
make docker-up       # Start Docker
make migrate        # Run migrations
make createsuper    # Create admin
make seed          # Seed test data
```

## 📊 Statistics

- **Python Files**: 45+
- **API Endpoints**: 30+
- **Database Models**: 8
- **Test Files**: 10+
- **Migrations**: 6
- **CI/CD Workflows**: 2
- **Supported Platforms**: 4

---

**Version**: 1.1.0  
**Last Updated**: 2026-04-18  
**Maintainer**: Smile Dangerous