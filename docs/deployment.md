# Deployment Guide

Complete deployment instructions for Smart LINE Bot + Dashboard + Scraper Pipeline.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- PostgreSQL 15+ (optional, using Docker)
- Redis 7+ (optional, using Docker)

## Quick Start (Docker Compose)

### 1. Clone and Setup
```bash
git clone https://github.com/Smiledangers/smart-line-automation-suite.git
cd smart-line-automation-suite

# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 2. Configure Environment
```env
# Required
LINE_CHANNEL_ACCESS_TOKEN=your_line_token
LINE_CHANNEL_SECRET=your_line_secret
OPENAI_API_KEY=your_openai_key

# Database
POSTGRES_PASSWORD=your_secure_password
SECRET_KEY=your_secret_key
```

### 3. Start Services
```bash
# Build and start all services
docker compose up -d --build

# Check status
docker compose ps
```

### 4. Initialize Database
```bash
# Run migrations
docker compose exec web alembic upgrade head

# Create superuser
docker compose exec web python scripts/create_superuser.py
```

### 5. Access Application
- API: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Production Deployment

### Using Docker Compose (Production)

```bash
# Create production compose file
cp docker-compose.yml docker-compose.prod.yml

# Edit for production
# - Use specific image tags
# - Enable health checks
# - Configure logging

# Start production
docker compose -f docker-compose.prod.yml up -d
```

### Using Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f deploy/k8s/

# Or use Helm
helm install demo-bot deploy/helm/demo-bot/
```

### Using Helm Chart

```bash
# Install Helm chart
helm install smart-line-bot deploy/helm/demo-bot/ \
  --set env.LINE_CHANNEL_ACCESS_TOKEN=xxx \
  --set env.LINE_CHANNEL_SECRET=xxx \
  --set env.OPENAI_API_KEY=xxx
```

### Using Cloud Platforms

#### Render.com
```bash
# Deploy using render.yaml
render deploy
```

#### Railway
```bash
# Deploy using railway.json
railway deploy
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LINE_CHANNEL_ACCESS_TOKEN` | Yes | LINE Messaging API token |
| `LINE_CHANNEL_SECRET` | Yes | LINE channel secret |
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `SECRET_KEY` | Yes | JWT signing key |
| `SENTRY_DSN` | No | Sentry error tracking |
| `SMTP_*` | No | Email configuration |

## Health Checks

```bash
# Check container health
docker compose ps

# Check application health
curl http://localhost:8000/health

# Check database
docker compose exec db pg_isready

# Check Redis
docker compose exec redis redis-cli ping
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker compose logs web

# Check environment
docker compose exec web env
```

### Database Connection Error
```bash
# Verify database is running
docker compose ps db

# Check connection
docker compose exec web python -c "from app.core.database import engine; engine.connect()"
```

### LINE Webhook Not Working
```bash
# Verify LINE credentials
docker compose exec web python -c "from app.core.config import settings; print(settings.LINE_CHANNEL_ACCESS_TOKEN)"
```

## Backup and Restore

### Backup Database
```bash
docker compose exec db pg_dump -U postgres demo_project > backup.sql
```

### Restore Database
```bash
docker compose exec -T db psql -U postgres demo_project < backup.sql
```

## Monitoring

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web
```

### Prometheus Metrics
```bash
# Access metrics
curl http://localhost:8000/metrics
```