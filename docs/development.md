# Development Guide

Complete guide for setting up and developing the Smart LINE Bot + Dashboard + Scraper Pipeline.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)
- LINE Developer Account
- OpenAI Account

## Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/Smiledangers/smart-line-automation-suite.git
cd smart-line-automation-suite
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
# Install all dependencies
pip install -r requirements/base.txt
pip install -r requirements/dev.txt

# Or use make
make install
make install-dev
```

### 4. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Required:
# - LINE_CHANNEL_ACCESS_TOKEN
# - LINE_CHANNEL_SECRET
# - OPENAI_API_KEY
# - SECRET_KEY
# - DATABASE_URL
# - REDIS_URL
```

### 5. Database Setup
```bash
# Initialize database
python scripts/init_db.py

# Run migrations
alembic upgrade head

# Create superuser
python scripts/create_superuser.py

# Seed test data (optional)
python scripts/seed_data.py --all
```

### 6. Run Development Server
```bash
# Start Redis (if not using Docker)
redis-server

# Start PostgreSQL (if not using Docker)
# Or use Docker:
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker (in separate terminal)
celery -A app.tasks.celery_app worker --loglevel=info

# Start Celery beat (in separate terminal)
celery -A app.tasks.celery_app beat --loglevel=info
```

### 7. Access Application
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

## Docker Development

### Quick Start
```bash
# Start all services
docker compose up -d --build

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Development Commands
```bash
# Rebuild containers
docker compose build --no-cache

# Run migrations
docker compose exec web alembic upgrade head

# Create superuser
docker compose exec web python scripts/create_superuser.py

# Access shell
docker compose exec web bash

# Run tests
docker compose exec web pytest
```

## Project Structure

```
app/
├── api/
│   └── v1/
│       └── endpoints/     # API route handlers
├── core/                   # Core configuration
├── models/                 # SQLAlchemy models
├── schemas/                # Pydantic schemas
├── services/               # Business logic
├── tasks/                  # Celery tasks
└── utils/                  # Utilities

tests/
├── unit/                   # Unit tests
├── integration/            # Integration tests
└── conftest.py             # Pytest fixtures

deploy/
├── k8s/                    # Kubernetes manifests
├── helm/                   # Helm charts
├── terraform/              # Terraform configs
└── cloud/                  # Cloud deployment configs
```

## Code Style

### Formatting
```bash
# Format code with Black
black app/ tests/

# Sort imports with isort
isort app/ tests/
```

### Type Checking
```bash
# Run mypy
mypy app/
```

### Linting
```bash
# Run flake8
flake8 app/ tests/
```

## Testing

### Run All Tests
```bash
pytest
```

### Run Specific Tests
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage
pytest --cov=app --cov-report=term-missing
```

### Test Fixtures
See `tests/conftest.py` for available fixtures:
- `client` - FastAPI test client
- `db_session` - Database session
- `test_user` - Test user
- `auth_headers` - Auth headers
- `sample_line_message` - LINE webhook sample
- `sample_scraping_job` - Scraping job sample

## Common Issues

### Database Connection Error
```bash
# Check PostgreSQL is running
pg_isready

# Check connection string in .env
```

### Redis Connection Error
```bash
# Check Redis is running
redis-cli ping

# Check REDIS_URL in .env
```

### LINE Webhook Not Working
```bash
# Verify credentials
python -c "from app.core.config import settings; print(settings.LINE_CHANNEL_ACCESS_TOKEN)"

# Use ngrok for local development
ngrok http 8000
# Update LINE webhook URL to ngrok URL
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements/base.txt

# Check PYTHONPATH
echo $PYTHONPATH
```

## Development Tips

1. **Use Docker** for consistent environment
2. **Use `make`** commands for common tasks (see Makefile)
3. **Write tests** before implementing features
4. **Use type hints** for better code documentation
5. **Keep secrets** in `.env`, never commit them
6. **Use `pre-commit`** hooks for code quality

## Contributing

1. Create feature branch
2. Write tests first
3. Implement feature
4. Run code formatters
5. Run full test suite
6. Push and create PR

## Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Celery Docs](https://docs.celeryproject.org/)
- [LINE Messaging API](https://developers.line.biz/en/docs/messaging-api/)
- [OpenAI API](https://platform.openai.com/docs/)