# ERP03 developer and CI entry points.
# Every target here mirrors a gate that runs in GitHub Actions.

.PHONY: help setup lint format test coverage build qualify up down clean env-setup container-push

help:
	@egrep -h '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup: ## Install backend and frontend dependencies
	python3 -m venv .venv && .venv/bin/pip install -r ERP-BACKEND/requirements.txt ruff
	cd frontend && npm install

lint: ## Run ruff + eslint + prettier checks
	.venv/bin/ruff check ERP-BACKEND/app ERP-BACKEND/tests ERP-BACKEND/alembic
	.venv/bin/ruff format --check ERP-BACKEND/app ERP-BACKEND/tests ERP-BACKEND/alembic
	cd frontend && npm run lint && npm run format:check

format: ## Apply ruff + prettier formatting
	.venv/bin/ruff format ERP-BACKEND/app ERP-BACKEND/tests ERP-BACKEND/alembic
	cd frontend && npm run format

test: ## Run backend tests (temporary SQLite database by default)
	cd ERP-BACKEND && DATABASE_PATH=$${DATABASE_PATH:-/tmp/erp03-dev.sqlite3} ../.venv/bin/pytest -q

coverage: ## Run backend tests with the coverage gate
	cd ERP-BACKEND && DATABASE_PATH=$${DATABASE_PATH:-/tmp/erp03-dev.sqlite3} \
		../.venv/bin/pytest -q --cov=app --cov-report=term-missing --cov-fail-under=70

build: ## Build frontend bundle
	cd frontend && npm run build

qualify: ## Canonical qualification used by CI
	bash scripts/qualify.sh

smoke: ## Smoke test a running stack (BASE_URL/FRONTEND_URL overridable)
	bash scripts/smoke.sh

up: ## Start the full local stack
	docker compose up --build -d

down: ## Stop the local stack and remove volumes
	docker compose down -v

env-setup: ## Configure registry credentials for container-push (.env.container)
	bash scripts/env-setup.sh

container-push: ## Build, scan and push current images (GHCR default; dockerhub supported)
	bash scripts/container-push.sh

clean: ## Remove build artifacts
	rm -rf frontend/dist .coverage ERP-BACKEND/.pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
