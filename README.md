# ERP03

Production-focused AI ERP modular-monolith foundation.

## Current runtime
- FastAPI API on port 8000
- React/Vite client served by nginx on 8080 in-container, exposed on host port 3000
- PostgreSQL and Redis services under Compose, schema migrations via Alembic
- Ollama sidecar provisioned for future AI work (configuration and port only today)
- Docker Compose for local system integration
- Deterministic Python and JavaScript dependency versions with committed lockfiles
- CI qualification for backend compile/tests (with a coverage gate) and frontend lint/build

## Repository layout
| Path | Purpose |
|---|---|
| `ERP-BACKEND/` | FastAPI application, Alembic migrations, backend tests |
| `frontend/` | Vite + React client, ESLint/Prettier configuration |
| `infra/kubernetes/` | Base manifests, dev/staging/production kustomize overlays, components |
| `infra/terraform/` | Provider-neutral module contracts and environment roots |
| `infra/monitoring/` | Prometheus scrape config, alert rules, Grafana dashboard |
| `.github/workflows/` | CI, Quality, Security, Container, IaC, Qualification, Release, Deploy, Rollback |
| `scripts/` | Qualification, backup, restore verification, smoke tests |
| `docs/` | Runbooks, release process, transaction integrity, readiness matrix |

## Verification endpoints
- `GET /api/v1` — API identity
- `GET /api/v1/healthz` — liveness
- `GET /api/v1/readyz` — database readiness and schema revision
- `GET /metrics` — Prometheus metrics

## Local run
```bash
cp .env.example .env          # then set SECRET_KEY and POSTGRES_PASSWORD
make up                       # docker compose up --build -d
make smoke                    # scripts/smoke.sh against the running stack
make down                     # docker compose down -v
```
Frontend: `http://localhost:3000` · API docs: `http://localhost:8000/docs`

Without Docker, the backend can be developed directly:
```bash
make setup        # venv + ruff + npm install
make lint         # ruff, eslint, prettier
make coverage     # pytest with the coverage gate (temporary SQLite database by default)
make build        # vite build
```

## Architecture direction
ERP remains the transactional authority. Business capabilities are added behind
explicit application/domain boundaries rather than splitting the system
prematurely into services.

Target capability sequence: authentication → business profile → capability
registry/compiler → policy/context → runtime/workflow → approvals/audit →
control tower → AI agent integration → end-to-end qualification.

## Deployment
Staging deploys automatically from `main`; production is promoted manually
through the protected `production` environment using the image digests that
staging validated. See `docs/DEPLOYMENT_RUNBOOK.md`, `docs/RELEASE_PROCESS.md`
and `docs/PRODUCTION_READINESS_MATRIX.md`.

### Container images
- GHCR (default): `Container` pushes `ghcr.io/<owner>/<repo>-{backend,frontend}`
  on every `main` push; `Container Push` (Actions → Run workflow) pushes the
  current branch on demand. GHCR needs no extra setup.
- Docker Hub: run `Container Push` with `registry: dockerhub` and set the
  repository secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`.
- Locally: `make env-setup && make container-push` (same build + Trivy scan gate).

## Security and operations
- Secrets are supplied at runtime through environment variables and a cluster
  `erp03-secrets` Secret; no secret belongs in this repository.
- Workflows run with least-privilege permissions and GitHub-owned, SHA-pinned
  actions only.
- Backups, restore verification, incident response and rollback each have a
  runbook in `docs/`.

Do not commit secrets. Configure runtime values through environment variables.
