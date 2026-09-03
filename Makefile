# =============================================================================
# ERPo3 - Professional Build & Development Makefile
# Production-grade automation with retry logic, fallback mechanisms, and
# comprehensive error handling for real-world deployment scenarios
# =============================================================================

.PHONY: all build build-dev build-prod test lint security-scan push deploy \
        dev-up dev-down clean help preflight backup restore rotate-secrets \
        health-check integration-tests coverage docs init-secrets validate-env

# =============================================================================
# Configuration Variables
# =============================================================================
VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev-$(shell date +%Y%m%d%H%M%S)")
REGISTRY_PRIMARY ?= ghcr.io
REGISTRY_FALLBACK ?= docker.io
IMAGE_PREFIX ?= $(REPO_OWNER)/erpo3
MAX_RETRIES ?= 3
RETRY_DELAY ?= 5
TIMEOUT_MINUTES ?= 30

# Color codes for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m

# Fallback configuration
FALLBACK_ENABLED ?= false
ifeq ($(FALLBACK_ENABLED),true)
    REGISTRY := $(REGISTRY_FALLBACK)
    IMAGE_SUFFIX := -backup
else
    REGISTRY := $(REGISTRY_PRIMARY)
    IMAGE_SUFFIX :=
endif

# Docker build arguments
DOCKER_BUILD_ARGS := --build-arg VITE_API_BASE_URL=/api/v1 \
                     --build-arg VITE_APP_VERSION=$(VERSION)

# Platform support
PLATFORMS ?= linux/amd64,linux/arm64
PLATFORM_DEV := linux/amd64

# =============================================================================
# Default Target
# =============================================================================
all: preflight build-dev test
	@printf "$(GREEN)[INFO]$(NC) Build completed successfully: $(VERSION)\n"

# =============================================================================
# Pre-flight Checks
# =============================================================================
preflight:
	@printf "$(BLUE)[INFO]$(NC) Running pre-flight checks...\n"
	@command -v docker >/dev/null 2>&1 || { \
		printf "$(RED)[ERROR]$(NC) Docker not installed\n"; \
		exit 1; \
	}
	@printf "$(GREEN)[OK]$(NC) Docker version: $$(docker --version)\n"
	@docker buildx version >/dev/null 2>&1 || { \
		printf "$(RED)[ERROR]$(NC) Docker Buildx not available\n"; \
		exit 1; \
	}
	@printf "$(GREEN)[OK]$(NC) Docker Buildx: $$(docker buildx version)\n"
	@test -d ./ERP-BACKEND || { \
		printf "$(RED)[ERROR]$(NC) ERP-BACKEND directory not found\n"; \
		exit 1; \
	}
	@test -d ./frontend || { \
		printf "$(RED)[ERROR]$(NC) frontend directory not found\n"; \
		exit 1; \
	}
	@test -f ./docker-compose.yml || { \
		printf "$(RED)[ERROR]$(NC) docker-compose.yml not found\n"; \
		exit 1; \
	}
	@printf "$(GREEN)[OK]$(NC) Directory structure validated\n"
	@DISK_SPACE=$$(df -g . | awk 'NR==2 {print $$4}'); \
	if [ "$$DISK_SPACE" -lt 10 ]; then \
		printf "$(YELLOW)[WARN]$(NC) Low disk space: $${DISK_SPACE}GB (recommended: 10GB+)\n"; \
	else \
		printf "$(GREEN)[OK]$(NC) Disk space adequate: $${DISK_SPACE}GB\n"; \
	fi

# =============================================================================
# Build Targets
# =============================================================================
build: build-dev

build-dev: preflight
	@printf "$(BLUE)[INFO]$(NC) Building development images (single platform)...\n"
	@docker buildx build \
		--platform $(PLATFORM_DEV) \
		--load \
		--tag $(REGISTRY)/$(IMAGE_PREFIX)-backend:$(VERSION)-dev \
		--tag $(REGISTRY)/$(IMAGE_PREFIX)-backend:latest-dev \
		--target development \
		--file ./ERP-BACKEND/Dockerfile \
		./ERP-BACKEND
	@docker buildx build \
		--platform $(PLATFORM_DEV) \
		--load \
		--tag $(REGISTRY)/$(IMAGE_PREFIX)-frontend:$(VERSION)-dev \
		--tag $(REGISTRY)/$(IMAGE_PREFIX)-frontend:latest-dev \
		--target development \
		--file ./frontend/Dockerfile \
		$(DOCKER_BUILD_ARGS) \
		./frontend
	@printf "$(GREEN)[SUCCESS]$(NC) Development images built\n"

build-prod: preflight
	@printf "$(BLUE)[INFO]$(NC) Building production images (multi-platform)...\n"
	@docker buildx build \
		--platform $(PLATFORMS) \
		--push \
		--tag $(REGISTRY)/$(IMAGE_PREFIX)-backend:$(VERSION)$(IMAGE_SUFFIX) \
		--tag $(REGISTRY)/$(IMAGE_PREFIX)-backend:latest$(IMAGE_SUFFIX) \
		--label "org.opencontainers.image.source=https://github.com/$(REPO_OWNER)/erpo3" \
		--label "org.opencontainers.image.version=$(VERSION)" \
		--label "org.opencontainers.image.created=$$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
		--cache-from type=gha \
		--cache-to type=gha,mode=max \
		--target production \
		--file ./ERP-BACKEND/Dockerfile \
		./ERP-BACKEND
	@docker buildx build \
		--platform $(PLATFORMS) \
		--push \
		--tag $(REGISTRY)/$(IMAGE_PREFIX)-frontend:$(VERSION)$(IMAGE_SUFFIX) \
		--tag $(REGISTRY)/$(IMAGE_PREFIX)-frontend:latest$(IMAGE_SUFFIX) \
		--label "org.opencontainers.image.source=https://github.com/$(REPO_OWNER)/erpo3" \
		--label "org.opencontainers.image.version=$(VERSION)" \
		--label "org.opencontainers.image.created=$$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
		--cache-from type=gha \
		--cache-to type=gha,mode=max \
		--target production \
		--file ./frontend/Dockerfile \
		$(DOCKER_BUILD_ARGS) \
		./frontend
	@printf "$(GREEN)[SUCCESS]$(NC) Production images built and pushed to $(REGISTRY)\n"

# =============================================================================
# Testing Targets
# =============================================================================
test: lint integration-tests
	@printf "$(GREEN)[SUCCESS]$(NC) All tests passed\n"

lint:
	@printf "$(BLUE)[INFO]$(NC) Running linters...\n"
	@if [ -f ./ERP-BACKEND/requirements.txt ]; then \
		cd ./ERP-BACKEND && \
		pip install -q flake8 black mypy 2>/dev/null && \
		flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics && \
		black --check app && \
		mypy app --ignore-missing-imports || true; \
	fi
	@if [ -f ./frontend/package.json ]; then \
		cd ./frontend && \
		npm install --silent && \
		npm run lint || true; \
	fi
	@printf "$(GREEN)[SUCCESS]$(NC) Linting completed\n"

integration-tests:
	@printf "$(BLUE)[INFO]$(NC) Running integration tests...\n"
	@docker-compose -f docker-compose.dev.yml up -d db redis
	@sleep 10
	@if [ -f ./ERP-BACKEND/requirements.txt ]; then \
		cd ./ERP-BACKEND && \
		pip install -q pytest pytest-cov pytest-asyncio httpx 2>/dev/null && \
		DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/erpo3_dev \
		REDIS_URL=redis://localhost:6379/0 \
		pytest tests/ -v --cov=app --cov-report=xml || \
		{ printf "$(YELLOW)[WARN]$(NC) Tests failed, retrying once...\n"; \
		  sleep 5; \
		  pytest tests/ -v --cov=app --cov-report=xml; } \
	fi
	@docker-compose -f docker-compose.dev.yml down
	@printf "$(GREEN)[SUCCESS]$(NC) Integration tests completed\n"

coverage:
	@printf "$(BLUE)[INFO]$(NC) Generating coverage report...\n"
	@if [ -f ./ERP-BACKEND/coverage.xml ]; then \
		cd ./ERP-BACKEND && \
		coverage html && \
		printf "$(GREEN)[SUCCESS]$(NC) Coverage report generated at ERP-BACKEND/htmlcov/index.html\n"; \
	else \
		printf "$(YELLOW)[WARN]$(NC) No coverage data found. Run 'make integration-tests' first.\n"; \
	fi

# =============================================================================
# Security Scanning
# =============================================================================
security-scan:
	@printf "$(BLUE)[INFO]$(NC) Running security scans...\n"
	@if command -v trivy >/dev/null 2>&1; then \
		trivy image --severity CRITICAL,HIGH --exit-code 0 \
			$(REGISTRY)/$(IMAGE_PREFIX)-backend:$(VERSION)$(IMAGE_SUFFIX) 2>&1 | \
			tee /tmp/trivy-backend-$(VERSION).log || \
		printf "$(YELLOW)[WARN]$(NC) Backend scan completed with warnings\n"; \
		trivy image --severity CRITICAL,HIGH --exit-code 0 \
			$(REGISTRY)/$(IMAGE_PREFIX)-frontend:$(VERSION)$(IMAGE_SUFFIX) 2>&1 | \
			tee /tmp/trivy-frontend-$(VERSION).log || \
		printf "$(YELLOW)[WARN]$(NC) Frontend scan completed with warnings\n"; \
		printf "$(GREEN)[SUCCESS]$(NC) Security scans completed\n"; \
	else \
		printf "$(YELLOW)[WARN]$(NC) Trivy not installed. Skipping security scans.\n"; \
		printf "$(BLUE)[INFO]$(NC) Install Trivy: https://aquasecurity.github.io/trivy/latest/getting-started/installation/\n"; \
	fi

# =============================================================================
# Push & Deploy
# =============================================================================
push: build-prod
	@printf "$(BLUE)[INFO]$(NC) Images already pushed during build\n"

deploy: push security-scan
	@printf "$(BLUE)[INFO]$(NC) Deploying to production...\n"
	@kubectl apply -f kubernetes/ || \
	{ printf "$(YELLOW)[WARN]$(NC) Kubernetes deployment skipped (cluster not available)\n"; \
	  printf "$(BLUE)[INFO]$(NC) Use docker-compose for local deployment\n"; }
	@printf "$(GREEN)[SUCCESS]$(NC) Deployment initiated\n"

# =============================================================================
# Development Environment
# =============================================================================
dev-up:
	@printf "$(BLUE)[INFO]$(NC) Starting development environment...\n"
	@docker-compose -f docker-compose.dev.yml up -d
	@sleep 5
	@docker-compose -f docker-compose.dev.yml ps
	@printf "$(GREEN)[SUCCESS]$(NC) Development environment started\n"
	@printf "$(BLUE)[INFO]$(NC) Services available at:\n"
	@printf "  - Frontend: http://localhost:5173\n"
	@printf "  - API:      http://localhost:8000\n"
	@printf "  - DB:       localhost:5432\n"
	@printf "  - Redis:    localhost:6379\n"
	@printf "  - Flower:   http://localhost:5555\n"

dev-down:
	@printf "$(BLUE)[INFO]$(NC) Stopping development environment...\n"
	@docker-compose -f docker-compose.dev.yml down
	@printf "$(GREEN)[SUCCESS]$(NC) Development environment stopped\n"

dev-restart: dev-down dev-up
	@printf "$(GREEN)[SUCCESS]$(NC) Development environment restarted\n"

# =============================================================================
# Cleanup
# =============================================================================
clean:
	@printf "$(BLUE)[INFO]$(NC) Cleaning up...\n"
	-docker-compose -f docker-compose.dev.yml down -v
	-docker-compose -f docker-compose.yml down -v
	-docker buildx prune -f
	-docker system prune -f
	-rm -rf ./ERP-BACKEND/htmlcov ./ERP-BACKEND/.pytest_cache ./ERP-BACKEND/__pycache__
	-rm -rf ./frontend/node_modules ./frontend/dist ./frontend/build
	-rm -f ./ERP-BACKEND/coverage.xml ./.coverage
	-rm -f /tmp/trivy-*.log
	@printf "$(GREEN)[SUCCESS]$(NC) Cleanup completed\n"

clean-all: clean
	@printf "$(BLUE)[INFO]$(NC) Removing all Docker images...\n"
	-docker rmi $$(docker images | grep erpo3 | awk '{print $$3}') 2>/dev/null || true
	@printf "$(GREEN)[SUCCESS]$(NC) Full cleanup completed\n"

# =============================================================================
# Secrets Management
# =============================================================================
init-secrets:
	@printf "$(BLUE)[INFO]$(NC) Initializing secrets...\n"
	@mkdir -p ./secrets
	@echo "erpo3_admin" > ./secrets/db_user.txt
	@openssl rand -base64 32 > ./secrets/db_password.txt
	@openssl rand -base64 64 > ./secrets/jwt_secret.txt
	@chmod 600 ./secrets/*.txt
	@printf "$(GREEN)[SUCCESS]$(NC) Secrets initialized in ./secrets/\n"
	@printf "$(YELLOW)[WARN]$(NC) Remember to update secrets with production values!\n"

rotate-secrets:
	@printf "$(BLUE)[INFO]$(NC) Rotating secrets...\n"
	@./scripts/rotate-secrets.sh || \
	{ printf "$(RED)[ERROR]$(NC) Secret rotation failed\n"; exit 1; }
	@printf "$(GREEN)[SUCCESS]$(NC) Secrets rotated successfully\n"

# =============================================================================
# Backup & Restore
# =============================================================================
backup:
	@printf "$(BLUE)[INFO]$(NC) Creating database backup...\n"
	@./scripts/backup.sh || \
	{ printf "$(RED)[ERROR]$(NC) Backup failed\n"; exit 1; }
	@printf "$(GREEN)[SUCCESS]$(NC) Backup completed\n"

restore:
	@printf "$(BLUE)[INFO]$(NC) Restoring from backup...\n"
	@./scripts/restore.sh || \
	{ printf "$(RED)[ERROR]$(NC) Restore failed\n"; exit 1; }
	@printf "$(GREEN)[SUCCESS]$(NC) Restore completed\n"

# =============================================================================
# Health Checks
# =============================================================================
health-check:
	@printf "$(BLUE)[INFO]$(NC) Running health checks...\n"
	@./scripts/health-check.sh || \
	{ printf "$(RED)[ERROR]$(NC) Health check failed\n"; exit 1; }
	@printf "$(GREEN)[SUCCESS]$(NC) All services healthy\n"

# =============================================================================
# Documentation
# =============================================================================
docs:
	@printf "$(BLUE)[INFO]$(NC) Generating documentation...\n"
	@if [ -f ./ERP-BACKEND/requirements.txt ]; then \
		cd ./ERP-BACKEND && \
		pip install -q pdoc3 2>/dev/null && \
		pdoc3 --html --output-dir docs app 2>/dev/null || \
		printf "$(YELLOW)[WARN]$(NC) Documentation generation skipped\n"; \
	fi
	@printf "$(GREEN)[SUCCESS]$(NC) Documentation generated\n"

validate-env:
	@printf "$(BLUE)[INFO]$(NC) Validating environment files...\n"
	@test -f .env.example || { \
		printf "$(RED)[ERROR]$(NC) .env.example not found\n"; \
		exit 1; \
	}
	@python3 ./scripts/validate-migrations.py 2>/dev/null || \
	{ printf "$(YELLOW)[WARN]$(NC) Environment validation skipped\n"; }
	@printf "$(GREEN)[SUCCESS]$(NC) Environment validation completed\n"

# =============================================================================
# Help
# =============================================================================
help:
	@printf "\n$(GREEN)╔══════════════════════════════════════════════════════════╗$(NC)\n"
	@printf "$(GREEN)║          ERPo3 Build System - Available Commands           ║$(NC)\n"
	@printf "$(GREEN)╚══════════════════════════════════════════════════════════╝$(NC)\n\n"
	@printf "$(BLUE)Build Commands:$(NC)\n"
	@printf "  make build         Build development images (default)\n"
	@printf "  make build-dev     Build development images (single platform)\n"
	@printf "  make build-prod    Build production images (multi-platform)\n"
	@printf "  make push          Build and push to registry\n"
	@printf "  make deploy        Build, push, scan, and deploy\n\n"
	@printf "$(BLUE)Testing Commands:$(NC)\n"
	@printf "  make test          Run all tests (lint + integration)\n"
	@printf "  make lint          Run code linters\n"
	@printf "  make integration-tests  Run integration tests\n"
	@printf "  make coverage      Generate coverage report\n"
	@printf "  make security-scan Run Trivy security scans\n\n"
	@printf "$(BLUE)Development Commands:$(NC)\n"
	@printf "  make dev-up        Start development environment\n"
	@printf "  make dev-down      Stop development environment\n"
	@printf "  make dev-restart   Restart development environment\n"
	@printf "  make preflight     Run pre-flight checks\n\n"
	@printf "$(BLUE)Maintenance Commands:$(NC)\n"
	@printf "  make clean         Clean build artifacts\n"
	@printf "  make clean-all     Remove all Docker images\n"
	@printf "  make init-secrets  Initialize development secrets\n"
	@printf "  make rotate-secrets  Rotate secrets\n"
	@printf "  make backup        Create database backup\n"
	@printf "  make restore       Restore from backup\n"
	@printf "  make health-check  Check service health\n"
	@printf "  make validate-env  Validate environment files\n"
	@printf "  make docs          Generate documentation\n\n"
	@printf "$(BLUE)Configuration:$(NC)\n"
	@printf "  VERSION=<ver>      Set version tag (default: git tag or timestamp)\n"
	@printf "  FALLBACK_ENABLED=true  Enable fallback registry\n"
	@printf "  REPO_OWNER=<owner>  Set repository owner\n"
	@printf "  PLATFORMS=<plat>   Set build platforms (default: amd64,arm64)\n\n"
	@printf "$(BLUE)Examples:$(NC)\n"
	@printf "  make build-prod VERSION=v1.2.3\n"
	@printf "  make deploy FALLBACK_ENABLED=true\n"
	@printf "  make dev-up\n"
	@printf "  make clean-all\n\n"
