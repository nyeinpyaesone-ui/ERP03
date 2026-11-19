# ERP03 Environment Configuration

Keep backend settings and Docker Compose interpolation variables separate. The backend uses
Pydantic Settings with `extra="forbid"`; do not put Compose-only values in
`ERP-BACKEND/.env`.

## Backend development environment

From the repository root:

```bash
cd ERP-BACKEND
cp .env.example .env
```

Edit `ERP-BACKEND/.env`. The checked-in template uses a repository-relative SQLite URL
(`sqlite+aiosqlite:///./.local/erp03.sqlite3`) suitable for host-side Alembic and Uvicorn
commands run from `ERP-BACKEND/`. Use only fields declared in
`ERP-BACKEND/app/core/config.py`.

## Docker Compose environment

From the repository root, copy the root template to the Compose-specific filename:

```bash
cp .env.example .env.compose
```

Set the Compose values in `.env.compose` (never commit it):

```ini
ERP03_ENVIRONMENT=development
SECRET_KEY=<generated-secret-at-least-32-characters>
POSTGRES_DB=erp03
POSTGRES_USER=erp03
POSTGRES_PASSWORD=<raw-postgres-password>
REDIS_PASSWORD=<redis-password>
DATABASE_URL=postgresql+asyncpg://erp03:<url-encoded-postgres-password>@postgres:5432/erp03
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

The password in `DATABASE_URL` must be URL-encoded (for example, `@` becomes `%40`,
`:` becomes `%3A`, and `%` becomes `%25`). Its decoded value must exactly match
`POSTGRES_PASSWORD`. The migration and backend services consume this same URL, avoiding
independent URL construction and password parsing differences.

Start the full stack:

```bash
docker compose --env-file .env.compose --profile full up --build -d
```

For production, set `ERP03_ENVIRONMENT=production`, use a strong unique signing key,
HTTPS-only CORS origins, and production database credentials. Do not reuse development
credentials.

## Container registry

The checked-in publishing workflows publish multi-architecture images to GHCR:

- `ghcr.io/nyeinpyaesone-ui/erp03-backend`
- `ghcr.io/nyeinpyaesone-ui/erp03-frontend`

They authenticate with the workflow-scoped `GITHUB_TOKEN` and
`packages: write`; no Docker Hub token or broad repository Actions permissions are needed
for these workflows.

## Kubernetes runtime secrets

The Kustomize base intentionally does not create `erp03-secrets`. Provision a Secret with
the required keys (`SECRET_KEY`, `POSTGRES_PASSWORD`, and `REDIS_PASSWORD`) in each target
namespace through the cluster's secret manager or the approved secure bootstrap procedure.
`infra/kubernetes/base/erp03-secrets.example.yaml` is documentation only and must not be
applied. Never commit real credentials or apply placeholder values.

## Verification

```bash
docker compose --env-file .env.compose config --quiet
kubectl kustomize infra/kubernetes/overlays/dev
kubectl kustomize infra/kubernetes/overlays/staging
kubectl kustomize infra/kubernetes/overlays/production
```

Do not apply production manifests until real runtime Secrets exist and the production image
digests have been copied from successful, verified GHCR publications.
