# ERP03 — Enterprise Resource Planning Platform

ERP03 is a modular ERP system of record with a FastAPI backend, React/Vite web frontend, PostgreSQL, Redis/Celery workers, Prometheus metrics, Docker Compose runtime, and Kubernetes/Terraform deployment foundations.

## Production engineering baseline

This repository is maintained with the following boundaries:

- ERP-BACKEND owns transactional business logic and the system of record.
- AI/integration components remain outside the ERP database boundary.
- Runtime credentials are supplied through environment variables, Docker secrets, Kubernetes Secrets, or an external secret manager.
- Production containers run as non-root users and use multi-stage builds.
- Health, readiness, metrics, dependency auditing, tests, container builds, and infrastructure validation are CI gates.
- Production deployment is an explicit, manual Kubernetes action; Terraform `apply` is never executed automatically by CI.

## Architecture

```text
Browser / Mobile / External Systems
                |
                v
        Ingress / Nginx
                |
        +-------+--------+
        |                |
        v                v
   React/Vite         FastAPI API
                         |
                 +-------+-------+
                 |               |
                 v               v
             PostgreSQL       Redis
                                 |
                                 v
                              Celery

AI / agent integrations communicate through authenticated API contracts;
they do not receive direct database access.
```

## Repository layout

```text
ERP03/
├── ERP-BACKEND/                  # FastAPI ERP core
├── frontend/                     # React + Vite web application
├── mobile/                       # Mobile application sources
├── infra/k8s/                    # Kubernetes base + production overlay
├── infra/terraform/              # Terraform production foundation
├── docker-compose.yml            # Secure local/production-like compose stack
├── docker-compose.prod.yml       # Existing image-based production variant
├── compose.production.yml        # Existing deployment variant
├── scripts/                      # Operational utilities
├── docs/                         # Architecture and operational docs
├── tests/                        # Repository-level tests
└── .github/workflows/ci.yml      # CI, security, build and deployment gates
```

## Local development

### Prerequisites

- Docker Engine + Docker Compose v2
- Python 3.12 for backend-only development
- Node.js 20 for frontend-only development

### Backend

```bash
cd ERP-BACKEND
cp .env.example .env
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

### Frontend

```bash
cd frontend
npm install
npm run lint
npm run build
```

### Compose

The canonical compose stack uses Docker secrets for the production-like API/database path. Create local secret files before starting it:

```bash
mkdir -p secrets
printf '%s' 'erp03' > secrets/db_user.txt
printf '%s' 'change-this-password' > secrets/db_password.txt
printf '%s' 'generate-a-random-secret-at-least-32-chars' > secrets/jwt_secret.txt
docker compose up --build
```

Do not commit those files.

## Runtime endpoints

| Component | Endpoint |
|---|---|
| API liveness | `GET /health` |
| API readiness | `GET /api/v1/health` |
| Prometheus metrics | `GET /metrics` |
| API docs | `/docs` |
| Web health | `GET /health` |

The readiness endpoint returns HTTP 503 when the database is unavailable. Kubernetes readiness probes should use it to prevent traffic from reaching an instance that cannot serve requests. Kubernetes liveness/startup probes use the lightweight `/health` endpoint.

## Security

### Secrets

The repository previously contained committed environment/secret material and local database/coverage artifacts. The production-hardening branch removes those files from the working tree and adds ignore rules for future credentials and runtime state.

**Important:** removing a secret from the current tree does not invalidate copies that may exist in Git history. Any credential that was ever real must be rotated/revoked outside GitHub.

Production secret sources:

- Docker Compose: `secrets/*` files created locally or by deployment automation.
- Kubernetes: `erp_solution-secrets` supplied by External Secrets Operator, Vault, AWS Secrets Manager, or another managed secret system.
- Terraform: sensitive variables supplied through a secure CI/CD variable or secret manager; never through committed `.tfvars` files.

See `infra/k8s/SECRET_PROVISIONING.md`.

### Container security

- Backend: Python 3.12 slim, multi-stage build, UID 10001, dropped Linux capabilities.
- Frontend: Node build stage and Nginx runtime, non-root runtime user.
- Compose services use `no-new-privileges` and capability dropping where applicable.
- Build contexts exclude `.env`, databases, coverage data, tests, and local caches.

### Application security

- JWT signing requires a secret of at least 32 characters.
- CORS is configurable rather than wildcarded.
- Request IDs and Prometheus HTTP metrics are emitted by the API.
- Rate limiting and authentication middleware are enabled in the FastAPI application.
- Nginx applies security response headers and a restrictive content-security policy.

## CI/CD

`.github/workflows/ci.yml` provides these gates:

1. Backend dependency audit, compile check and pytest.
2. Frontend dependency audit, ESLint and production build.
3. Terraform validation and Kubernetes Kustomize rendering.
4. Pull-request dependency review.
5. Main-branch container publication to GHCR using immutable commit-SHA tags.
6. Manual Kubernetes deployment through the `production` environment.

Cloud credentials are not embedded in the workflow. Kubernetes deployment requires the `KUBE_CONFIG_DATA` environment secret and explicit `deploy=true` workflow input.

GitHub repository settings should additionally require the CI workflow before merging to `main`, require at least one review, dismiss stale approvals, and prevent force pushes/deletions on `main`.

## Kubernetes

Production manifests live under `infra/k8s/`.

The production overlay provides:

- FastAPI API deployment with startup/liveness/readiness probes.
- React/Nginx web deployment with health probes.
- Celery worker deployment.
- PostgreSQL and Redis stateful workloads for the self-hosted deployment path.
- Prometheus scrape annotations on the API.
- Network, RBAC and ingress resources already present in the base.

Production credentials are deliberately excluded from the Kustomization. See `infra/k8s/SECRET_PROVISIONING.md`.

Before applying to a cluster:

```bash
kubectl kustomize infra/k8s/overlays/production
```

Never apply an unreviewed rendered manifest to production.

## Terraform

Terraform production foundations are under `infra/terraform/environments/production` and currently cover VPC, RDS, ElastiCache and encrypted/versioned S3 backup storage.

CI validates Terraform with:

```bash
terraform init -backend=false
terraform validate
```

For a shared production environment, configure a remote encrypted backend with state locking before `plan`/`apply`. Terraform state must not be committed to Git. Do not run `terraform apply` without an explicit operational approval.

Typical controlled workflow:

```bash
terraform init
terraform plan -var-file=production.tfvars
# review plan
terraform apply -var-file=production.tfvars
```

## Observability

The API exposes Prometheus metrics at `/metrics`. The HTTP middleware records request count, status and latency with request IDs. Production Kubernetes resources can scrape the endpoint using the existing Prometheus annotations.

For a full production observability stack, connect the metrics endpoint to Prometheus and configure alerting for:

- API 5xx rate
- API latency
- readiness failures
- database connection failures
- worker queue depth/task failures
- container restarts
- PostgreSQL storage and replication health

## Database migrations

Migrations are executed as a dedicated Compose `migrate` service before the API and worker start. This avoids having every API replica independently attempt schema migration at startup.

In Kubernetes, migrations should be run as a controlled release job before switching application traffic to a new schema-dependent version.

## Supply-chain and dependency management

- Python dependencies are pinned in `ERP-BACKEND/requirements.txt`.
- Frontend dependencies are declared in `frontend/package.json`; the repository currently does not carry a generated frontend lockfile, so CI/builds use `npm install` rather than falsely claiming `npm ci` reproducibility.
- Dependabot is enabled for Python, npm, Docker and GitHub Actions dependencies.
- CI performs Python and npm vulnerability audits.

A generated `frontend/package-lock.json` should be added once dependency installation is performed in a network-enabled development/CI environment; after that, switch the frontend build and CI to `npm ci` and enforce lockfile consistency.

## Release discipline

Use Conventional Commits and short-lived branches. Production changes should merge through a reviewed pull request with all CI gates passing.

Recommended branch policy:

- `main` is protected.
- No direct pushes.
- Required CI status checks.
- At least one approving review.
- Force-push and branch deletion disabled.
- Production deployment performed from an approved main commit.

## Current status

This repository is being hardened at the **Platform Bootstrap / Engineering Foundation** stage. The objective of this stage is to make the engineering foundation deterministic and operationally safe before expanding ERP business functionality.

Next engineering priorities are verification of the CI pipeline, dependency remediation reported by audits, generation/commitment of the frontend lockfile, production secret-manager integration, and controlled Kubernetes/Terraform environment validation.
