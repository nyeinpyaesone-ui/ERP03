.PHONY: dev test lint build up down agent-bootstrap agent-verify agent-evidence

dev:
	docker compose -f docker-compose.dev.yml up --build

up:
	docker compose -f docker-compose.dev.yml up -d

down:
	docker compose -f docker-compose.dev.yml down

lint:
	cd ERP-BACKEND && ruff check app tests alembic
	cd ERP-BACKEND && ruff format --check app tests alembic

test:
	cd ERP-BACKEND && pytest -q

build:
	docker compose -f docker-compose.dev.yml build

build-backend:
	docker build -t erp03-backend:dev ERP-BACKEND

build-frontend:
	docker build -t erp03-frontend:dev frontend

build-all:
	docker build -t erp03-backend:dev ERP-BACKEND
	docker build -t erp03-frontend:dev frontend

agent-bootstrap:
	bash scripts/agent/bootstrap.sh

agent-verify:
	bash scripts/agent/verify.sh

agent-evidence:
	@latest=$$(ls -1t .agent/evidence/*.json 2>/dev/null | head -1); \
	[ -n "$$latest" ] && cat "$$latest" || echo "no evidence yet"
