# ERP03 Environment Configuration

This document describes the current repository layout. For production rollout details, use [the zero-downtime deployment runbook](ZERO_DOWNTIME_DEPLOYMENT_2026-11.md).

## Local setup

### Backend-only development

```bash
cd ERP-BACKEND
cp .env.example .env
mkdir -p .local
# Set DATABASE_URL in .env to this host-writable SQLite file before migrating:
# DATABASE_URL=sqlite+aiosqlite:///./.local/erp03.sqlite3
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r dev-requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Only use keys declared in `ERP-BACKEND/app/core/config.py`; unknown keys are rejected by settings validation.

### Full Docker Compose stack

Compose variable substitution reads the repository-root `.env`. Create that file locally (never commit it) with:

```ini
POSTGRES_DB=erp03
POSTGRES_USER=erp03
POSTGRES_PASSWORD=<local-password>
SECRET_KEY=<random-secret-at-least-32-characters>
# Local-only setting: allows localhost CORS. Deployed environments default to production.
ERP03_ENVIRONMENT=development
# POSTGRES_PASSWORD must match the URL-decoded password in DATABASE_URL.
# Use single quotes around values containing '
```

Then start the full profile:

```bash
docker compose --profile full up --build
```

## Container registry and staging delivery

The publishing workflows push to GHCR:
- `ghcr.io/nyeinpyaesone-ui/erp03-backend`
- `ghcr.io/nyeinpyaesone-ui/erp03-frontend`

They use the scoped GitHub Actions `GITHUB_TOKEN`, not `DOCKERHUB_TOKEN`. The backend and frontend images are built for AMD64 and ARM64.

The manual `.github/workflows/deploy-staging.yml` workflow accepts a source SHA plus backend and frontend digests and deploys those immutable images over SSH to a Docker Compose staging host. It runs the migration service, checks container health and attempts to restore the prior images if deployment fails. Configure the SSH and read-only GHCR Environment secrets listed in [CONFIGURATION_SETUP.md](../CONFIGURATION_SETUP.md). This is not a multi-replica or zero-downtime deployment.

## Runtime secret management

Kubernetes namespaces require an externally provisioned `erp03-secrets` Secret with `SECRET_KEY`, `POSTGRES_PASSWORD` and `REDIS_PASSWORD`. The example manifest is not part of the applied Kustomize resources. Use a cluster secret manager or the controlled process in the zero-downtime runbook.

## Health endpoints

- `GET /api/v1/healthz` — process liveness.
- `GET /api/v1/readyz` — checks PostgreSQL connectivity and that an Alembic revision exists. It does **not** compare the recorded revision with the current migration head; a ready response does not prove migrations are current.
- `GET /` — frontend Nginx health.

Redis is not part of `readyz` because the current rate limiter has a fail-open circuit breaker. The Redis client uses the configured `REDIS_MAX_CONNECTIONS` (default 50 per process), 2-second connection/operation timeouts and a 30-second health check; it closes its pool on graceful shutdown. Monitor Redis degradation and connection-pool exhaustion separately.

## Local qualification

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

## Important production limitation

The backend journal still uses SQLite on a ReadWriteOnce PVC, while the production overlay uses multiple backend replicas and an HPA. The checked-in PostgreSQL and Redis Kubernetes resources are single-instance. The production deployment script is not fully wired to the supplied image digest and still has placeholder verification steps. These are unresolved availability constraints; rolling application settings alone do not make the whole ERP zero-downtime.
 to prevent Compose interpolation.
POSTGRES_PASSWORD='<local-password>'
SECRET_KEY=<random-secret-at-least-32-characters>
DATABASE_URL=postgresql+asyncpg://erp03:<url-encoded-password>@postgres:5432/erp03
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
REDIS_PASSWORD='<local-redis-password>'
```

Then start the full profile:

```bash
docker compose --profile full up --build
```

## Container registry and staging delivery

The publishing workflows push to GHCR:
- `ghcr.io/nyeinpyaesone-ui/erp03-backend`
- `ghcr.io/nyeinpyaesone-ui/erp03-frontend`

They use the scoped GitHub Actions `GITHUB_TOKEN`, not `DOCKERHUB_TOKEN`. The backend and frontend images are built for AMD64 and ARM64.

The manual `.github/workflows/deploy-staging.yml` workflow accepts a source SHA plus backend and frontend digests and deploys those immutable images over SSH to a Docker Compose staging host. It runs the migration service, checks container health and attempts to restore the prior images if deployment fails. Configure the SSH and read-only GHCR Environment secrets listed in [CONFIGURATION_SETUP.md](../CONFIGURATION_SETUP.md). This is not a multi-replica or zero-downtime deployment.

## Runtime secret management

Kubernetes namespaces require an externally provisioned `erp03-secrets` Secret with `SECRET_KEY`, `POSTGRES_PASSWORD` and `REDIS_PASSWORD`. The example manifest is not part of the applied Kustomize resources. Use a cluster secret manager or the controlled process in the zero-downtime runbook.

## Health endpoints

- `GET /api/v1/healthz` — process liveness.
- `GET /api/v1/readyz` — PostgreSQL and migration readiness.
- `GET /` — frontend Nginx health.

Redis is not part of `readyz` because the current rate limiter has a fail-open circuit breaker. The Redis client uses the configured `REDIS_MAX_CONNECTIONS` (default 50 per process), 2-second connection/operation timeouts and a 30-second health check; it closes its pool on graceful shutdown. Monitor Redis degradation and connection-pool exhaustion separately.

## Local qualification

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

## Important production limitation

The backend journal still uses SQLite on a ReadWriteOnce PVC, while the production overlay uses multiple backend replicas and an HPA. The checked-in PostgreSQL and Redis Kubernetes resources are single-instance. The production deployment script is not fully wired to the supplied image digest and still has placeholder verification steps. These are unresolved availability constraints; rolling application settings alone do not make the whole ERP zero-downtime.
