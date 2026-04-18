# Makefile for Smart LINE Bot

.PHONY: help install install-dev test test-cov lint format clean docker-up docker-down docker-logs

# Default target
help:
	@echo "Smart LINE Bot - Available Commands"
	@echo "====================================="
	@echo "make install        - Install production dependencies"
	@echo "make install-dev     - Install development dependencies"
	@echo "make test           - Run tests"
	@echo "make test-cov       - Run tests with coverage"
	@echo "make lint           - Run linters (black, isort, flake8)"
	@echo "make format         - Format code (black, isort)"
	@echo "make type-check     - Run type checker (mypy)"
	@echo "make clean          - Clean up cache and build files"
	@echo "make docker-up      - Start Docker containers"
	@echo "make docker-down    - Stop Docker containers"
	@echo "make docker-logs    - Show Docker logs"
	@echo "make migrate        - Run database migrations"
	@echo "make createsuper   - Create superuser"
	@echo "make seed           - Seed test data"
	@echo "make shell          - Run Python shell"
	@echo "make run            - Run development server"

# Installation
install:
	pip install -r requirements/base.txt

install-dev:
	pip install -r requirements/base.txt
	pip install -r requirements/dev.txt

# Testing
test:
	pytest

test-cov:
	pytest --cov=app --cov-report=term-missing --cov-report=html

# Linting and formatting
lint:
	@echo "Running black..."
	@black --check app/ tests/ || true
	@echo "Running isort..."
	@isort --check-only app/ tests/ || true
	@echo "Running flake8..."
	@flake8 app/ tests/ || true

format:
	black app/ tests/
	isort app/ tests/

type-check:
	mypy app/ --ignore-missing-imports --no-error-summary

# Clean up
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache 2>/dev/null || true
	rm -rf htmlcov 2>/dev/null || true
	rm -rf .coverage 2>/dev/null || true

# Docker
docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-ps:
	docker compose ps

# Database
migrate:
	docker compose exec web alembic upgrade head

migrate-create:
	docker compose exec web alembic revision --autogenerate -m "$(MESSAGE)"

createsuper:
	docker compose exec web python scripts/create_superuser.py

seed:
	docker compose exec web python scripts/seed_data.py --all

reset-db:
	docker compose exec web python scripts/reset_db.py --force

# Development
shell:
	docker compose exec web python -c "import IPython; IPython.start_ipython()"

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	celery -A app.tasks.celery_app worker --loglevel=info

beat:
	celery -A app.tasks.celery_app beat --loglevel=info

# Health check
health:
	curl -s http://localhost:8000/health | python -m json.tool

# Deploy
deploy-staging:
	docker compose -f docker-compose.staging.yml up -d --build

deploy-prod:
	docker compose -f docker-compose.prod.yml up -d --build