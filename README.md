# Smart LINE Bot + Dashboard + Scraper Pipeline

## 🎯 Project Overview

This is a complete intelligent LINE Bot system that combines a backend dashboard, automated scraping pipeline, and AI services. The project uses modern Python tech stack to provide production-ready features and deployment options.

## 🧩 System Architecture

### Core Components
1. **LINE Bot Integration** - Using LINE Messaging API for message sending/receiving
2. **Backend Dashboard** - Management interface for user statistics and system monitoring
3. **Automated Scraping Pipeline** - Schedule-based scraping system using Botsaurus
4. **AI Service Integration** - LangGraph architecture for asynchronous AI processing
5. **Celery Task Queue** - Handles time-consuming operations (scraping, AI computation, notification sending)
6. **PostgreSQL + Redis** - Primary database and caching layer

## 🚀 Quick Start

### Using Docker Compose (Recommended)

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env file and fill in required keys:
#    LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, OPENAI_API_KEY, etc.

# 3. Build and start all services
docker-compose up -d --build

# 4. Run database migrations
docker-compose exec web alembic upgrade head

# 5. Create admin account
docker-compose exec web python scripts/create_superuser.py

# 6. Access the application
#    API Docs: http://localhost:8000/docs
#    Health Check: http://localhost:8000/health
```

### Local Development (No Docker)

```bash
# 1. Create Python virtual environment
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 2. Install dependencies
pip install -r requirements/base.txt
pip install -r requirements/dev.txt  # Includes testing tools

# 3. Set environment variables
cp .env.example .env
# Edit .env to fill in required keys

# 4. Initialize database
python scripts/init_db.py

# 5. Run migrations
alembic upgrade head

# 6. Create superuser
python scripts/create_superuser.py

# 7. Start application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📁 Project Structure

```
demo_project/
├── app/
│   ├── api/v1/endpoints/   # API endpoints (line, dashboard, scraping, ai, auth, system, monitoring)
│   ├── core/               # Core (config, database, security)
│   ├── Models/             # SQLAlchemy models (user, line_user, scraping_job, ai_conversation)
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business services (line, dashboard, scraping, ai)
│   ├── tasks/              # Celery tasks with beat schedule
│   ├── monitoring/         # Prometheus metrics
│   └── main.py             # FastAPI entry point
├── scraper/                # Scraping framework (Botsaurus)
├── alembic/versions/       # Database migrations
├── requirements/           # Dependencies
├── scripts/                # Helper scripts (create_superuser, init_db, backup, generate_test_data)
├── deploy/                 # Deployment (k8s, helm, terraform, cloud)
├── tests/                  # Test suite (unit + integration)
├── docs/                   # Documentation (api, architecture, deployment, development, changelog)
├── .github/workflows/      # GitHub Actions CI/CD
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── pyproject.toml
```

## ⭐ Key Features

### LINE Bot
- Message receiving and replying
- User management and binding
- Circuit Breaker protection for external API calls
- Quick replies and menu interactions
- Button template messages
- Reply messages support

### Backend Dashboard
- User CRUD operations
- System statistics and monitoring
- Operation logs and audit trail
- Real-time stats (user count, LINE users, jobs, AI conversations)

### Automated Scraping Pipeline
- Job creation and scheduling (Celery beat)
- Multi-website scraping support
- Automatic result storage
- Error retry and notification
- Job status tracking (pending, running, completed, failed, cancelled)

### AI Service
- LangGraph conversation flows
- Async database integration
- Conversation history management
- Multi-model support (GPT-4, GPT-3.5)
- Circuit breaker protection

### Infrastructure
- Complete Alembic database migrations (3 migrations)
- Redis as Celery broker
- Comprehensive testing framework (unit + integration)
- Docker Compose & Kubernetes & Helm support
- GitHub Actions CI/CD pipelines
- Prometheus metrics and monitoring endpoints
- Health check, readiness check, startup check
- Makefile for common commands
- Database backup/restore scripts
- Test data generator

### Security
- JWT authentication with access/refresh tokens
- Password hashing with bcrypt
- OAuth2 password flow
- Role-based access control
- CORS configuration

## 🔧 Configuration

All settings can be adjusted in `.env`, refer to `.env.example`:
- **Required**: LINE keys, OPENAI_API_KEY, DATABASE_URL, REDIS_URL, SECRET_KEY
- **Optional**: SMTP settings, Sentry, Prometheus, scraping parameters

## 🧪 Testing

```bash
# Run all tests
pytest

# Run by category
pytest tests/unit/
pytest tests/integration/

# With coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_services.py -v
```

## 📦 Deployment Options

- **Development**: `docker-compose up -d`
- **Production**: `docker-compose -f docker-compose.prod.yml up -d`
- **Kubernetes**: `kubectl apply -f deploy/k8s/`
- **Helm**: `helm install demo-bot ./deploy/helm/demo-bot/`
- **Terraform**: `cd deploy/terraform && terraform init`
- **Cloud**: Render.com (`deploy/render.yaml`) or Railway.app (`deploy/railway.json`)

## 🔨 Development Commands (Makefile)

```bash
make install         # Install dependencies
make test            # Run tests
make lint            # Run linters
make format          # Format code
make docker-up       # Start Docker
make migrate         # Run migrations
make createsuper     # Create superuser
make seed            # Seed test data
```

---

## 📊 Statistics (v1.0.0)

- **Python Files**: 33+
- **API Endpoints**: 20+
- **Database Models**: 6
- **Test Files**: 8+
- **Migrations**: 3
- **CI/CD Workflows**: 2

**Project Location**: `C:\Users\user\.openclaw\workspace\demo_project`  
**Version**: 1.0.0  
**Last Updated**: 2026-04-18  
**Maintainer**: Smile Dangerous