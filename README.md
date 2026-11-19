# ERP03 — Production-Focused AI ERP Modular Monolith

[![CI](https://github.com/nyeinpyaesone-ui/ERP03/actions/workflows/ci.yml/badge.svg)](https://github.com/nyeinpyaesone-ui/ERP03/actions/workflows/ci.yml)
[![Quality](https://github.com/nyeinpyaesone-ui/ERP03/actions/workflows/quality.yml/badge.svg)](https://github.com/nyeinpyaesone-ui/ERP03/actions/workflows/quality.yml)
[![Security](https://github.com/nyeinpyaesone-ui/ERP03/actions/workflows/security.yml/badge.svg)](https://github.com/nyeinpyaesone-ui/ERP03/actions/workflows/security.yml)

## Overview

ERP03 is a multi-tenant business ERP implemented as a modular monolith. The frontend is React/Vite; the API and domain services run in FastAPI. PostgreSQL is the authoritative relational store, Redis supports distributed rate limiting, and the current transaction-intent journal is a separate SQLite component with a documented multi-replica limitation.

## Current technology baseline

| Layer | Technology |
|---|---|
| Backend runtime | Python 3.12.13 slim |
| API | FastAPI 0.162.0, Uvicorn 0.54.0 |
| ORM / migrations | SQLAlchemy 2.1.8 async, Alembic 1.20.1 |
| Database | PostgreSQL 15; SQLite for local journal/development paths |
| Cache / rate limit | Redis server 7.4 in Kubernetes; redis-py 8.1.0 |
| Frontend | React 19.3.1, Vite 8.3.6 |
| Frontend runtime | unprivileged Nginx 1.27 Alpine |
| Infrastructure | Docker Compose, Kubernetes, Kustomize, Terraform |
| Observability | Prometheus metrics, request IDs, audit logging, optional OpenTelemetry |
| AI integration | Optional TypeSafe System One integration |

## Quick start

### Automated setup

```bash
./scripts/setup.sh
./scripts/setup.sh --with-infra
./scripts/setup.sh --qualify
```

### Manual backend setup

```bash
cd ERP-BACKEND
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r dev-requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm ci
npm run build
npm run dev
```

### Vercel frontend deployment

The Vercel frontend uses the repository-level `api/[...path].js` function as a same-origin API proxy. Configure `ERP03_BACKEND_ORIGIN` in the Vercel project's Production, Preview and Development environments as the HTTPS origin of the deployed FastAPI service (origin only; no `/api/v1` path and no credentials). The proxy maps `/api/*` to the backend's `/api/v1/*`, forwards authentication and idempotency headers, disables response caching, and applies a 30-second upstream timeout and 4 MiB request-body limit.

Do not commit the backend origin or credentials to the repository. A missing variable returns an explicit `503`; it does not silently route API calls to the frontend static host. Verify `GET /api/healthz` and an authenticated login flow on a Vercel Preview deployment before promoting it.

### Docker Compose

```bash
# Minimal local stack
docker compose up --build

# PostgreSQL + Redis + migration profile
docker compose --profile full up --build

# Development hot reload
docker compose -f docker-compose.dev.yml up --build
```

See [Configuration & Credentials](CONFIGURATION_SETUP.md) before setting production secrets or container publishing.

## Architecture

The backend keeps transport, schemas, domain services, persistence and operational concerns in separate modules:

```text
ERP-BACKEND/app/
├── api/       # auth, catalog, sales, purchasing, transactions, health
├── schemas/   # validated request/response contracts
├── services/  # business rules, inventory, orchestration, RBAC
├── models/    # identity, ERP and operations models
├── db/        # async SQLAlchemy engine/session
└── core/      # config, security, audit, metrics, errors, journal, AI adapter
```

The application remains a modular monolith. Add queues or independently deployed services only when measured workload or ownership boundaries justify them.

## Core capabilities

- Tenant-scoped authentication and authorization.
- Sales, catalog, purchasing and inventory domain operations.
- Idempotent transaction orchestration and journal records.
- PostgreSQL transactions, migrations and row-level concurrency controls.
- Redis sorted-set distributed rate limiting with fail-open circuit-breaker behavior.
- Request IDs, structured logs, audit records and protected Prometheus metrics.
- Optional TypeSafe integration outside authoritative domain commit decisions.

## Verification endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/v1` | API identity |
| `GET /api/v1/healthz` | Process liveness |
| `GET /api/v1/readyz` | PostgreSQL/schema readiness |
| `GET /metrics` | Protected Prometheus metrics |
| `GET /docs` | OpenAPI documentation |

Redis is intentionally not part of the readiness probe while its current rate-limiter integration can fail open. The backend now bounds each Redis client pool with `REDIS_MAX_CONNECTIONS` (default 50), uses explicit 2-second connect/operation timeouts and a 30-second health check, and closes the pool during graceful shutdown. Redis degradation must be monitored and alerted separately.

## CI, container publishing and staging deployment

- Backend image: `ghcr.io/nyeinpyaesone-ui/erp03-backend`
- Frontend image: `ghcr.io/nyeinpyaesone-ui/erp03-frontend`
- Images are built for Linux AMD64 and ARM64.
- GitHub Actions uses scoped `GITHUB_TOKEN` package permissions; no Docker Hub token is required by the current GHCR publishing workflows.
- Production Kubernetes images must be pinned by real build digests, not mutable `latest` tags.

The manual `.github/workflows/deploy-staging.yml` workflow accepts a source commit and both image digests, connects over SSH, deploys to a Docker Compose staging host, runs migrations, checks container health and attempts image rollback on failure. This is a single-host staging flow; it is not a Kubernetes deployment and does not provide a multi-replica zero-downtime guarantee.

The production shell deployment script is not yet qualified: its digest verification and endpoint smoke-test steps are placeholders, and the production manifests still require real image digests. Do not use it for a production cutover until those issues and the stateful-data blockers are resolved.

## Kubernetes

Base manifests and environment overlays are located in `infra/kubernetes/`:

```bash
kubectl kustomize infra/kubernetes/overlays/dev
kubectl kustomize infra/kubernetes/overlays/staging
kubectl kustomize infra/kubernetes/overlays/production
```

Provision runtime secrets outside Git before applying any environment. The placeholder template is intentionally excluded from the Kustomize resource list. PostgreSQL, Redis and Ollama image digest placeholders also require real, verified digests before applying the Kubernetes manifests.

**Production is not yet zero-downtime qualified.** The current SQLite journal uses a ReadWriteOnce volume while the backend scales to multiple replicas; PostgreSQL and Redis manifests are also single-instance. See the deployment runbook before applying production resources.

## Documentation

- [Engineering Roadmap](docs/ROADMAP.md)
- [Performance Optimisation Checklist](docs/PERFORMANCE_OPTIMIZATION_CHECKLIST.md)
- [Documentation Guidelines](docs/DOCUMENTATION_GUIDELINES.md)
- [Architecture Blueprint — November 2026](docs/ARCHITECTURE_BLUEPRINT_2026-11.md)
- [Zero-Downtime Deployment and Runtime Configuration](docs/ZERO_DOWNTIME_DEPLOYMENT_2026-11.md)
- [Configuration & Credentials Setup](CONFIGURATION_SETUP.md)
- [Deployment Runbook](docs/DEPLOY_RUNBOOK.md)
- [Production Readiness Matrix](docs/PRODUCTION_READINESS_MATRIX.md)
- [Current Remediation Tracker](docs/TODO.md)
- [Historical Remaining Tasks](docs/REMAINING_TASKS.md)
- [Security Policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## Qualification

```bash
cd ERP-BACKEND
ruff check app tests alembic
ruff format --check app tests alembic
python -m compileall -q app alembic
alembic upgrade head
pytest -q

cd ../frontend
npm ci
npm run build
```
