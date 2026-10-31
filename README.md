# ERP03 — Production-Focused AI ERP Modular Monolith

[![CI](https://github.com/nyeinpyaesone-ui/ERP03/actions/workflows/ci.yml/badge.svg)](https://github.com/nyeinpyaesone-ui/ERP03/actions/workflows/ci.yml)
[![Quality](https://github.com/nyeinpyaesone-ui/ERP03/actions/workflows/quality.yml/badge.svg)](https://github.com/nyeinpyaesone-ui/ERP03/actions/workflows/quality.yml)
[![Security](https://github.com/nyeinpyaesone-ui/ERP03/actions/workflows/security.yml/badge.svg)](https://github.com/nyeinpyaesone-ui/ERP03/actions/workflows/security.yml)

## Overview

ERP03 is a production-focused AI ERP modular monolith built with FastAPI (backend) and React/Vite (frontend). It provides a foundation for enterprise resource planning with explicit domain boundaries, idempotent transactions, and production-grade infrastructure.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.116, Python 3.12, SQLAlchemy 2.0, Alembic |
| Frontend | React 19, Vite 7, nginx (production) |
| Database | PostgreSQL 15 (production), SQLite (development) |
| Cache/Rate Limit | Redis 7 (sorted sets, sliding window) |
| Infra | Terraform, Kubernetes, Docker, Docker Compose |
| Observability | Prometheus, OpenTelemetry, Grafana |
| AI | TypeSafe System One (optional) |

## Quick Start

### Prerequisites
- Python ≥ 3.12
- Node.js ≥ 18
- Docker (optional, for full stack)

### Automated Setup
```bash
./scripts/setup.sh                # toolchain detection, venv, deps, secure .env, smoke tests
./scripts/setup.sh --with-infra   # additionally start Docker Compose stack
./scripts/setup.sh --qualify      # run full CI-equivalent qualification gate
```

### Manual Setup
```bash
# Backend
cd ERP-BACKEND
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r dev-requirements.txt
cp .env.example .env  # edit with your values
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm ci
npm run build
```

### Docker Compose
```bash
# Minimal (backend + frontend + SQLite)
docker compose up --build

# Full (with PostgreSQL + Redis + migrations)
docker compose --profile full up

# Development (with HMR)
docker compose -f docker-compose.dev.yml up --build
```

## Verification Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1` | API identity |
| `GET /api/v1/healthz` | Liveness probe |
| `GET /api/v1/readyz` | Transactional DB + migration readiness |
| `GET /metrics` | Prometheus metrics (bearer token auth) |
| `GET /docs` | OpenAPI documentation |

## Architecture

Modular monolith — business capabilities behind explicit app/domain boundaries:

```
app/
├── api/          # REST endpoints (auth, catalog, sales, purchasing, transactions, health)
├── core/         # Config, errors, security, metrics, typesafe, transaction store
├── db/           # SQLAlchemy session factory
├── models/       # ORM models (identity, erp, operations)
├── schemas/      # Pydantic request/response schemas
└── services/     # Domain logic (sales, catalog, inventory, orchestration, rbac, bootstrap)
```

Target capability sequence: authentication → business profile → capability registry → policy/context → runtime/workflow → approvals/audit → control tower → AI agent integration → E2E qualification.

## Key Features

- **Idempotent POS Sales** — SHA-256 fingerprint verification, branch-row locking, savepoints per payment
- **Cross-Module Orchestration** — 6-state lifecycle (PENDING → PROCESSING → COMMITTED/FAILED → RECONCILIATION_REQUIRED → CANCELLED)
- **Redis Rate Limiting** — Distributed sliding window using sorted sets
- **TypeSafe Integration** — Optional AI judgment layer with confidence thresholds
- **Production Security** — JWT auth, tenant-scoped queries, non-root containers, NetworkPolicy, RBAC
- **Observability** — Request IDs, structured logging, Prometheus metrics, OpenTelemetry
- **Backup/Restore** — Automated backups with checksum verification and restore scripts

## Development

### Qualification Gate
```bash
cd ERP-BACKEND
ruff check app tests alembic
ruff format --check app tests alembic
python -m compileall -q app alembic
alembic upgrade head
pytest -q
```

### Frontend Build
```bash
cd frontend
npm ci && npm run build
```

### Scripts
| Script | Purpose |
|--------|---------|
| `scripts/setup.sh` | Bootstrap development environment |
| `scripts/doctor.sh` | Repository health check |
| `scripts/qualify.sh` | CI-equivalent qualification gate |
| `scripts/preflight.sh` | Production pre-flight validation |
| `scripts/security-audit.sh` | Security scan |
| `scripts/backup.sh` | Database backup |
| `scripts/restore.sh` | Database restore |
| `scripts/deploy-production.sh` | Production deployment |
| `scripts/rollback.sh` | Production rollback |

## Environment Variables

See `.env.example` for all available configuration options. Key variables:

- `SECRET_KEY` — ≥32 characters (production)
- `DATABASE_URL` — PostgreSQL for production, SQLite for dev
- `CORS_ORIGINS` — Comma-separated origins
- `REDIS_URL` — Redis connection URL
- `ENVIRONMENT` — development/staging/production

## Kubernetes

Base manifests in `infra/kubernetes/base/` with overlays for dev, staging, and production:

```bash
# Validate manifests
python -c "import yaml; [yaml.safe_load_all(open(f)) for f in __import__('glob').glob('infra/kubernetes/**/*.yaml', recursive=True)]"

# Apply (requires kubectl)
kubectl apply -k infra/kubernetes/overlays/production/
```

## Documentation

- [AGENTS.md](AGENTS.md) — Developer instructions
- [SECURITY.md](SECURITY.md) — Security policy
- [CHANGELOG.md](CHANGELOG.md) — Change history
- [docs/TODO.md](docs/TODO.md) — Remediation tracker
- [docs/PRODUCTION_READINESS_MATRIX.md](docs/PRODUCTION_READINESS_MATRIX.md) — Production readiness
- [docs/adr/](docs/adr/) — Architecture Decision Records

## License

See [LICENSE](LICENSE) for details.
