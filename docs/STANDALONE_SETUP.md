# ERP03 standalone local runtime

This profile runs the existing FastAPI backend and React/Nginx frontend without requiring a PostgreSQL server, Redis, Kubernetes, cloud credentials, or an external AI provider.

## Requirements

- Docker Engine with the Docker Compose v2 plugin
- Python 3 (only used by the setup script to generate a local signing key)
- curl

## Start

From the repository root:

```bash
bash scripts/setup-standalone.sh
```

The script creates `.env.standalone` with mode 0600 if it does not already exist, validates the Compose model, builds both images, runs Alembic migrations, waits for API readiness, and smoke-tests the frontend.

Open:

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- API readiness: http://localhost:8000/api/v1/readyz

Set `ERP03_HTTP_PORT=3100` before running the setup script to use another frontend port. The backend remains bound to loopback on port 8000.

## Runtime design

- The backend uses SQLite for local domain data and a separate SQLite file for the transaction-intent journal.
- Both files live in the named `erp03_standalone_data` volume.
- Redis rate limiting is disabled in this local-only profile; no Redis service is started.
- The frontend Nginx configuration proxies `/api/*` to the backend service.
- Alembic runs as a one-shot migration service before the API starts.
- Containers restart automatically after a process failure. Health checks cover API readiness and frontend HTTP serving.

This is a developer/demo standalone profile, not a production topology. SQLite journal state is not a shared multi-replica store. Do not use this profile for production, multi-node deployment, or production backup/restore testing. Use the PostgreSQL + Redis Compose profile or the reviewed Kubernetes environment for integration/staging, and resolve the journal and database availability blockers before production rollout.

## Stop and preserve data

```bash
docker compose --project-name erp03-standalone --env-file .env.standalone -f docker-compose.standalone.yml down
```

The named volume is intentionally retained. To permanently delete local ERP data, run `docker compose --project-name erp03-standalone --env-file .env.standalone -f docker-compose.standalone.yml down --volumes`. This destructive option is not part of normal shutdown.

Do not commit `.env.standalone`. It is covered by the repository's `.env.*` ignore rule. The generated key is local-only and must not be reused in staging or production.
