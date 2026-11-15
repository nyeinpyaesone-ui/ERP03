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

Redis is intentionally not part of the readiness probe while its current rate-limiter integration can fail open. Redis degradation must be monitored and alerted separately.

## CI and container publishing

- Backend image: `ghcr.io/nyeinpyaesone-ui/erp03-backend`
- Frontend image: `ghcr.io/nyeinpyaesone-ui/erp03-frontend`
- Images are built for Linux AMD64 and ARM64.
- GitHub Actions uses scoped `GITHUB_TOKEN` package permissions; no Docker Hub token is required by the current GHCR publishing workflows.
- Production Kubernetes images must be pinned by real build digests, not mutable `latest` tags.

The checked-in Docker workflows publish images; they do not, by themselves, prove a Kubernetes deployment was completed.

## Kubernetes

Base manifests and environment overlays are located in `infra/kubernetes/`:

```bash
kubectl kustomize infra/kubernetes/overlays/dev
kubectl kustomize infra/kubernetes/overlays/staging
kubectl kustomize infra/kubernetes/overlays/production
```

Provision runtime secrets outside Git before applying any environment. The placeholder template is intentionally excluded from the Kustomize resource list.

**Production is not yet zero-downtime qualified.** The current SQLite journal uses a ReadWriteOnce volume while the backend scales to multiple replicas; PostgreSQL and Redis manifests are also single-instance. See the deployment runbook before applying production resources.

## Documentation

- [Architecture Blueprint — November 2026](docs/ARCHITECTURE_BLUEPRINT_2026-11.md)
- [Zero-Downtime Deployment and Runtime Configuration](docs/ZERO_DOWNTIME_DEPLOYMENT_2026-11.md)
- [Configuration & Credentials Setup](CONFIGURATION_SETUP.md)
- [Deployment Runbook](docs/DEPLOY_RUNBOOK.md)
- [Production Readiness Matrix](docs/PRODUCTION_READINESS_MATRIX.md)
- [Remediation Tracker](docs/REMAINING_TASKS.md)
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
