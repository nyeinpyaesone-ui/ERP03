# ERP03 — Configuration & Credentials Setup

**Repository:** `nyeinpyaesone-ui/ERP03`  
**Current image registry:** GitHub Container Registry (GHCR)  
**Application model:** FastAPI + React/Vite modular monolith

This guide replaces the older Docker Hub instructions. Configure secrets in the relevant runtime environment; do not commit credentials or generated secret files.

## 1. Image publishing and GitHub permissions

Current workflows:
- `.github/workflows/docker-publish.yml` builds `ghcr.io/nyeinpyaesone-ui/erp03-backend`.
- `.github/workflows/container.yml` builds `ghcr.io/nyeinpyaesone-ui/erp03-frontend`.

Both publish Linux AMD64 and ARM64 images. The backend workflow uses keyless Cosign signing and verifies its image signature; both workflows publish SBOM/provenance metadata and verify the architecture manifest.

The workflows use the automatically provided `GITHUB_TOKEN` with explicit `packages: write` permission. **Do not configure `DOCKERHUB_TOKEN` for these GHCR workflows.** Keep repository Actions default permissions restrictive; do not enable broad write permissions just to make image publishing work.

Verify that both GHCR packages are associated with this repository. If a target Kubernetes cluster cannot pull the packages anonymously, provision a namespace-scoped GHCR pull secret through the cluster secret manager and reference it in the pod specs.

## 2. GitHub Actions secrets

For the current build-and-publish workflows, no database password, application signing key or Docker Hub credential is required. Runtime secrets belong in Kubernetes / Docker Compose, not in the image build pipeline.

Only add GitHub Environment secrets when a reviewed deployment workflow explicitly consumes them. Any future Kubernetes deploy identity must be short-lived and namespace-scoped, with production environment approval.

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

The workflows publish branch, release-tag, SHA and (for main) latest tags. The production overlay is intended to pin each image by digest:

- `ghcr.io/nyeinpyaesone-ui/erp03-backend@sha256:<verified-digest>`
- `ghcr.io/nyeinpyaesone-ui/erp03-frontend@sha256:<verified-digest>`

Replace the explicit placeholders in `infra/kubernetes/overlays/production/kustomization.yaml` only with the digests reported by successful image-publish workflow runs. Never infer a digest from a tag or an earlier build.

## 6. Verification checklist

- [ ] CI, Quality, Security, Container, Docker, Type Check and Coverage pass for the exact release commit.
- [ ] Policy Enforcement completes with a successful job (not `startup_failure` / no jobs).
- [ ] Both GHCR images exist and include AMD64 + ARM64 manifests.
- [ ] Image digests are copied from the exact successful build.
- [ ] Kubernetes runtime Secret exists in the target namespace, provisioned outside Git.
- [ ] The target cluster can pull the images.
- [ ] Staging rollout, smoke tests, backup/restore and rollback drill pass.
- [ ] SQLite journal / RWO storage and database HA blockers are resolved before production zero-downtime qualification.

## 7. Production status

The repository includes Kubernetes Deployment, HPA, PDB, Service, Ingress and probe configuration. It does not currently provide evidence that an ERP03 production cluster is live, that production database failover works, or that the multi-replica SQLite journal is safe. Do not label production as zero-downtime qualified until those conditions are tested and recorded.
