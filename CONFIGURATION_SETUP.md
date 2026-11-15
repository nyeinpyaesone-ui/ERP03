# ERP03 — Configuration & Credentials Setup

**Repository:** `nyeinpyaesone-ui/ERP03`  
**Current image registry:** GitHub Container Registry (GHCR)  
**Application model:** FastAPI + React/Vite modular monolith

This guide replaces older Docker Hub instructions. Configure credentials only in the relevant runtime environment; do not commit secrets or generated runtime files.

## 1. Image publishing and GitHub permissions

Current publishing workflows:
- `.github/workflows/docker-publish.yml` builds `ghcr.io/nyeinpyaesone-ui/erp03-backend`.
- `.github/workflows/container.yml` builds `ghcr.io/nyeinpyaesone-ui/erp03-frontend`.

Both publish Linux AMD64 and ARM64 images. Backend publishing uses keyless Cosign signing and verifies its signature. Both workflows produce SBOM/provenance metadata and verify architecture manifests.

The workflows use the automatically provided `GITHUB_TOKEN` with explicit `packages: write` permission. **Do not configure `DOCKERHUB_TOKEN` for these GHCR workflows.** Keep repository Actions default permissions restrictive; do not enable broad write permissions just to make image publishing work.

Verify that both GHCR packages are associated with this repository. If a target host or Kubernetes cluster cannot pull the packages anonymously, provision a narrowly scoped read-only GHCR credential in that runtime environment.

## 2. Manual staging deployment workflow

The repository contains `.github/workflows/deploy-staging.yml`. It is triggered manually from the `main` branch and deploys immutable GHCR image digests to a remote Docker Compose staging host over SSH.

Configure these GitHub Environment secrets in the `staging` environment:

| Secret | Purpose |
|---|---|
| `STAGING_SSH_PRIVATE_KEY` | SSH private key used by the runner |
| `STAGING_SSH_KNOWN_HOSTS` | Pinned host key; do not disable host verification |
| `STAGING_SSH_HOST` | Staging host |
| `STAGING_SSH_USER` | Restricted deployment user |
| `STAGING_SSH_PORT` | SSH port; optional, defaults to 22 |
| `STAGING_GHCR_USERNAME` | GHCR account used by the remote host |
| `STAGING_GHCR_READ_TOKEN` | Read-only GHCR token with `read:packages` |

Configure the `STAGING_DEPLOY_PATH` GitHub Environment variable to the existing checkout directory containing the Compose file on the staging host.

The manual workflow requires three inputs:
- `source_sha`: full 40-character commit SHA.
- `backend_digest`: exact backend OCI digest, formatted `sha256:<64 lowercase hex>`.
- `frontend_digest`: exact frontend OCI digest, formatted `sha256:<64 lowercase hex>`.

The workflow checks the source/image revision labels, requires a previously running backend and frontend for rollback, executes the migration service, updates the application containers, waits for health checks, and attempts to restore prior images on failure. The staging host must have the expected Compose file, Docker Engine, Compose plugin, a clean checkout and a healthy previous application release.

This workflow is a single-host Docker Compose deployment. It has no multi-replica service strategy and must not be described as zero downtime. Do not put database passwords or the application signing key in GitHub Actions unless a future reviewed workflow explicitly needs them.

## 3. Local Docker Compose configuration

The repository-root `.env` is used for Compose variable substitution. Keep it out of Git and restrict file permissions.

Example key names (use fresh local values):

```ini
POSTGRES_DB=erp03
POSTGRES_USER=erp03
POSTGRES_PASSWORD=<local-postgres-password>
SECRET_KEY=<random-secret-at-least-32-characters>
DATABASE_URL=postgresql+asyncpg://erp03:<url-encoded-password>@postgres:5432/erp03
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
REDIS_PASSWORD=<local-redis-password>
IMAGE_TAG=latest
```

For local backend development without Compose, copy `ERP-BACKEND/.env.example` to `ERP-BACKEND/.env` and set the fields declared in `ERP-BACKEND/app/core/config.py`. Settings use `extra="forbid"`; do not add undeclared environment variables to that file.

For production, use HTTPS-only `CORS_ORIGINS`, PostgreSQL (never SQLite as the primary domain database), a unique signing key and distinct database/cache passwords.

## 4. Kubernetes runtime secrets

Kubernetes uses a Secret named `erp03-secrets` in each namespace. Required keys:
- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`

The old checked-in placeholder was removed from the base Kustomize resource list. The file `infra/kubernetes/base/erp03-secrets.example.yaml` is documentation only and must not be applied. Provision the real Secret through External Secrets Operator / your secret manager, or the secure manual bootstrap in [the zero-downtime runbook](docs/ZERO_DOWNTIME_DEPLOYMENT_2026-11.md).

Use unique credentials per environment. Never place the values in a manifest, GitHub issue, workflow summary, shell history or committed `.env`.

## 5. Image tags and digests

The workflows publish branch, release-tag, SHA and (for main) latest tags. The production overlay pins the backend and frontend by digest. The Kubernetes base also contains digest placeholders for PostgreSQL, Redis and Ollama. Replace every `REPLACE_WITH_REAL_DIGEST` / `REPLACE_WITH_REAL_*_DIGEST` marker with the digest verified for that exact image version before applying the corresponding Kustomize overlay.

- `ghcr.io/nyeinpyaesone-ui/erp03-backend@sha256:<verified-digest>`
- `ghcr.io/nyeinpyaesone-ui/erp03-frontend@sha256:<verified-digest>`

Never infer a digest from a tag or an earlier build. Keep the production web images immutable and pinned to the exact published release.

## 6. Verification checklist

- [ ] CI, Quality, Security, Container, Docker, Type Check and Coverage pass for the exact release commit.
- [ ] Policy Enforcement completes with a successful job (not `startup_failure` / no jobs).
- [ ] Both GHCR images exist and include AMD64 + ARM64 manifests.
- [ ] Image digests are copied from the exact successful build.
- [ ] Staging Environment secrets and `STAGING_DEPLOY_PATH` are configured for the manual staging workflow.
- [ ] Kubernetes runtime Secret exists in the target namespace, provisioned outside Git.
- [ ] The target host/cluster can pull the images.
- [ ] Staging deployment, smoke tests, backup/restore and rollback drill pass.
- [ ] SQLite journal / RWO storage and database HA blockers are resolved before production zero-downtime qualification.

## 7. Production status

The repository includes Kubernetes Deployment, HPA, PDB, Service, Ingress and probe configuration, plus a manual Docker Compose staging deployment workflow. The production deployment shell script still contains placeholder digest verification and health-check steps, and the checked-in Kubernetes images contain digest placeholders. The connected Railway project inspected for this task is a separate ERPNext/MariaDB environment, not an ERP03 deployment.

There is no evidence here that an ERP03 production cluster is live, that production database failover works, or that the multi-replica SQLite journal is safe. Do not label production as zero-downtime qualified until those conditions are tested and recorded.
