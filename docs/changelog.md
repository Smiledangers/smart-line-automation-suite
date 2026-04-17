# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-18

### Added

#### Core Features
- **LINE Bot Integration**
  - Webhook handling for LINE messages
  - User authentication and binding
  - Text, flex, and template message support
  - OAuth flow for LINE Login
  - Rich menu and quick reply support

- **Backend Dashboard**
  - User management (CRUD)
  - System statistics and monitoring
  - Operation logs and audit trail
  - Data export functionality

- **Automated Scraping Pipeline**
  - Job creation and scheduling (Celery)
  - Botsaurus integration
  - Multi-website support
  - Result storage and retrieval
  - Error retry and notification

- **AI Service**
  - LangGraph agent integration
  - Conversation management
  - OpenAI API integration
  - Async processing with Celery

#### Infrastructure
- **Docker Compose** - Full stack (web, worker, beat, redis, postgres)
- **Kubernetes** - Deployment manifests
- **Helm Chart** - Production-ready Helm deployment
- **Terraform** - AWS ECS deployment
- **PostgreSQL** - Primary database with Alembic migrations
- **Redis** - Cache and Celery broker

#### Security
- JWT authentication with access/refresh tokens
- Password hashing with bcrypt
- OAuth2 password flow
- Role-based access control
- CORS configuration

#### Monitoring & Logging
- Structured logging with request ID tracking
- Health check endpoints (/health, /ready)
- Prometheus metrics endpoint
- Circuit breaker for external APIs
- Error tracking with Sentry support

#### Testing
- Pytest configuration
- Unit tests for services
- Integration tests for API endpoints
- Fixtures for database and authentication

### Configuration
- Pydantic settings with environment variable support
- Complete .env.example with all required variables
- Type hints throughout the codebase

### Project Structure
```
demo_project/
├── app/
│   ├── api/v1/endpoints/   # 6 API routers
│   ├── core/               # Config, database, security
│   ├── models/             # 6 SQLAlchemy models
│   ├── schemas/            # 4 Pydantic schema modules
│   ├── services/            # 4 business services
│   ├── tasks/               # Celery tasks & beat schedule
│   └── utils/               # Validators, logging, circuit breaker
├── deploy/
│   ├── k8s/                # Kubernetes manifests
│   ├── helm/               # Helm charts
│   ├── terraform/           # Terraform AWS ECS
│   └── cloud/               # Render.com config
├── tests/
│   ├── unit/               # 4 unit test files
│   └── integration/         # 3 integration test files
├── scripts/                 # 5 utility scripts
├── docs/                    # 4 documentation files
├── alembic/                 # Database migrations
└── scraper/                 # Botsaurus scraper
```

### Known Issues
- Some placeholder code in task helpers needs real implementation
- Live demo deployment not yet available

### Dependencies
- FastAPI 0.115.0
- SQLAlchemy 2.0.36
- Celery 5.4.0
- LINE Bot SDK 3.8.0
- OpenAI 1.57.4
- Pydantic 2.10.3

---

## Upgrade Notes

### From 0.x to 1.0.0
1. Update environment variables (see .env.example)
2. Run database migrations: `alembic upgrade head`
3. Rebuild Docker containers: `docker compose up -d --build`
4. Create superuser: `python scripts/create_superuser.py`

## Migration Guides

### Adding New Model
1. Create model in `app/Models/`
2. Create schema in `app/schemas/`
3. Create/update migration: `alembic revision --autogenerate -m "Add new model"`
4. Run migration: `alembic upgrade head`
5. Add service methods in `app/services/`

### Adding New API Endpoint
1. Create endpoint in `app/api/v1/endpoints/`
2. Add router to `app/api/v1/router.py`
3. Add tests in `tests/integration/`

### Adding New Celery Task
1. Add task in `app/tasks/celery_app.py`
2. Add to beat schedule if needed
3. Add tests in `tests/unit/`