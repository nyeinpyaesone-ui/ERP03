# ERP03 Enterprise Build System
# Reusable, production-grade build targets for development, testing, deployment
# Usage: make [target]

DOCKER_COMPOSE := docker compose
PYTHON := python3
ALEMBIC := alembic
DOCKER_REGISTRY ?= ghcr.io
IMAGE_NAME ?= erp03/backend
FRONTEND_IMAGE ?= erp03/frontend
VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "latest")
COMPOSE_FILE ?= docker-compose.yml

.PHONY: help dev prod test migrate up down logs shell db-shell backup restore health stop clean push seed all

all: test ## Default target: run tests

help: ## Display this help message
	@echo "ERP03 Enterprise Build System"
	@echo "=============================="
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  dev       - Start development environment (PostgreSQL + Redis)"
	@echo "  prod      - Start production environment with all services"
	@echo "  test      - Run full test suite"
	@echo "  migrate   - Run database migrations"
	@echo "  up        - Start all Docker services in background"
	@echo "  down      - Stop all Docker services"
	@echo "  logs      - Follow service logs"
	@echo "  shell     - Open bash shell in backend container"
	@echo "  db-shell  - Open psql shell in database"
	@echo "  backup    - Create database backup"
	@echo "  restore   - Restore database from backup"
	@echo "  health    - Check service health"
	@echo "  stop      - Stop all services"
	@echo "  clean     - Clean build artifacts and volumes"
	@echo "  push      - Build and push Docker images to registry"
	@echo "  seed      - Seed database with initial data"
	@echo ""

dev: ## Start development environment with PostgreSQL and Redis
	@echo "Starting development environment..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d postgres redis
	@sleep 5
	@echo "Running database migrations..."
	cd ERP-BACKEND && $(ALEMBIC) upgrade head
	@echo ""
	@echo "✓ Development environment ready"
	@echo "  Backend: http://localhost:8000"
	@echo "  Frontend: http://localhost:3000"
	@echo "  PostgreSQL: localhost:5432"
	@echo "  Redis: localhost:6379"

prod: ## Start production environment with all services
	@echo "Starting production environment..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -f docker-compose.prod.yml up -d --build
	@echo ""
	@echo "✓ Production environment started"
	@echo "  Waiting for services to be healthy..."
	@sleep 10
	@$(MAKE) health

test: ## Run full test suite with coverage
	@echo "Running tests..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) run --rm backend pytest -v --cov=app --cov-report=term-missing
	@echo ""
	@echo "✓ Tests complete"

migrate: ## Run database migrations
	@echo "Running database migrations..."
	cd ERP-BACKEND && $(ALEMBIC) upgrade head
	@echo "✓ Migrations complete"

up: ## Start all services in background
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d
	@echo "✓ Services started"

down: ## Stop all services
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down
	@echo "✓ Services stopped"

logs: ## Follow service logs
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f

shell: ## Open bash shell in backend container
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) exec backend bash

db-shell: ## Open psql shell in PostgreSQL database
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) exec postgres psql -U erpuser -d erpdb

backup: ## Create database backup
	@mkdir -p ./backups
	@docker exec $$(docker ps -q -f name=postgres) pg_dump -U erpuser erpdb > ./backups/erpdb-$$(date +%Y%m%d-%H%M%S).sql
	@echo "✓ Backup created: ./backups/erpdb-$$(date +%Y%m%d-%H%M%S).sql"

restore: ## Restore database from backup (usage: make restore FILE=./backups/file.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE parameter required. Usage: make restore FILE=./backups/file.sql"; \
		exit 1; \
	fi
	cat $(FILE) | docker exec -i $$(docker ps -q -f name=postgres) psql -U erpuser -d erpdb
	@echo "✓ Database restored from $(FILE)"

health: ## Check service health
	@echo "Checking service health..."
	@sleep 10
	@curl -f http://localhost:8000/api/v1/health || (echo "✗ Backend unhealthy" && exit 1)
	@echo "✓ Backend healthy"
	@curl -f http://localhost:3000 || (echo "✗ Frontend unhealthy" && exit 1)
	@echo "✓ Frontend healthy"
	@echo ""
	@echo "All services healthy"

stop: ## Stop all services
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down

clean: ## Clean build artifacts, containers, and volumes
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "Stopping containers..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down -v --remove-orphans
	@echo "Pruning build cache..."
	docker builder prune -f
	@echo ""
	@echo "✓ Clean complete"

push: ## Build and push Docker images to registry
	@echo "Building and pushing images to $(DOCKER_REGISTRY)..."
	@echo "Version: $(VERSION)"
	docker buildx build --platform linux/amd64,linux/arm64 \
		-t $(DOCKER_REGISTRY)/$(IMAGE_NAME):$(VERSION) \
		-t $(DOCKER_REGISTRY)/$(IMAGE_NAME):latest \
		-f ERP-BACKEND/Dockerfile . \
		--push
	docker buildx build --platform linux/amd64,linux/arm64 \
		-t $(DOCKER_REGISTRY)/$(FRONTEND_IMAGE):$(VERSION) \
		-t $(DOCKER_REGISTRY)/$(FRONTEND_IMAGE):latest \
		-f frontend/Dockerfile . \
		--push
	@echo ""
	@echo "✓ Images pushed successfully"
	@echo "  Backend: $(DOCKER_REGISTRY)/$(IMAGE_NAME):$(VERSION)"
	@echo "  Frontend: $(DOCKER_REGISTRY)/$(FRONTEND_IMAGE):$(VERSION)"

seed: ## Seed database with initial data
	@echo "Seeding database..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) run --rm backend python -m app.scripts.seed_data
	@echo "✓ Database seeded"
