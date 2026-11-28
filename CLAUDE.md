# ERP03 — Project Context

## Repository
- Purpose: Production-focused AI ERP modular-monolith foundation (FastAPI backend + React/Vite frontend + Terraform infra)
- Primary application: ERP03 API + POS/web client
- Source of truth: repository + tracked documentation

## Stack
- Runtime: Python 3.12.13, Node 22
- Framework: FastAPI 0.116.1, Uvicorn, SQLAlchemy 2.0, Alembic, React 19, Vite 7
- Database: PostgreSQL 15 (production), SQLite (dev/journal fallback)
- Container: Docker Compose, non-root app user

## Required Checks
- `cd ERP-BACKEND && ruff check app tests alembic`
- `cd ERP-BACKEND && ruff format --check app tests alembic`
- `cd ERP-BACKEND && python -m compileall -q app alembic`
- `cd ERP-BACKEND && alembic upgrade head` (fresh DB)
- `cd ERP-BACKEND && pytest -q` (49 passed, 1 PG-only skip)
- `cd frontend && npm ci --no-audit --no-fund && npm run build`
- `docker compose -f docker-compose.yml config --quiet`
- `docker compose -f docker-compose.dev.yml config --quiet`

## Engineering Rules
- Inspect existing code before adding new abstractions.
- Preserve public APIs unless the task explicitly changes them.
- Validate external input at trust boundaries.
- Never commit secrets. Use `ERP-BACKEND/.env.example` and `.env.compose.example`.
- Prefer reversible migrations.
- Do not claim completion without verification evidence.
- Settings uses `extra="forbid"` — only declared fields may appear in `.env`.

## Verification Endpoints
- `GET /api/v1` — API identity
- `GET /api/v1/healthz` — liveness
- `GET /api/v1/readyz` — database + migration readiness
- `GET /api/v1/docs` — API docs
- `GET /api/v1/metrics` — Prometheus (bearer token required)
