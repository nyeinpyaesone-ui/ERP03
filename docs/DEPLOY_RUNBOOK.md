# ERP03 Deployment Runbook — Current State

**Repository baseline inspected:** `main` at `716f305f` (2026-11-12)  
**Purpose:** describe the real build, staging and production delivery paths.  
**Production status:** not zero-downtime qualified.

This replaces the historical runbook steps tied to old commit `b639c2d6`, old PR numbers and old release assumptions. Do not run the old merge/issue-close command sequence.

## 1. Actual delivery components

| Component | Current implementation |
|---|---|
| Backend image publish | `.github/workflows/docker-publish.yml` → GHCR |
| Frontend image publish | `.github/workflows/container.yml` → GHCR |
| Staging delivery | Manual `.github/workflows/deploy-staging.yml` → SSH → single-host Docker Compose |
| Kubernetes config | `infra/kubernetes/base` and dev/staging/production overlays |
| Production deploy script | `scripts/deploy-production.sh`; currently not qualified for a release |
| Rollback script | `scripts/rollback.sh`; GHCR image namespace is aligned in this branch |

Images:
- `ghcr.io/nyeinpyaesone-ui/erp03-backend`
- `ghcr.io/nyeinpyaesone-ui/erp03-frontend`

The image workflows build AMD64 and ARM64 images. Backend publish also performs keyless Cosign signing/verification. Use the immutable digest reported by the exact successful workflow run.

## 2. Before staging

1. Refresh `main` and record the release commit SHA.
2. Review all PRs that affect transaction integrity, authentication, database pool sizing, migrations or manifests.
3. Require CI, Quality, Security, Container, Docker, Type Check, Coverage and Agent Parity checks to pass for the exact commit.
4. Require Policy Enforcement to complete successfully with an actual job. `startup_failure` with no jobs is not a pass.
5. Verify backend and frontend image digests and architecture manifests.
6. Confirm the staging host has the expected Compose file, Docker Engine and Compose plugin, clean checkout, secrets and a healthy previous release.

Local qualification:

```bash
./scripts/qualify.sh
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

Use the repository's actual scripts and requirements; do not rely on historical test counts in older deployment notes.

## 3. Staging deployment

Configure the `staging` GitHub Environment as documented in [Configuration & Credentials](../CONFIGURATION_SETUP.md):
- `STAGING_SSH_PRIVATE_KEY`
- `STAGING_SSH_KNOWN_HOSTS`
- `STAGING_SSH_HOST`
- `STAGING_SSH_USER`
- `STAGING_SSH_PORT` (optional)
- `STAGING_GHCR_USERNAME`
- `STAGING_GHCR_READ_TOKEN` with `read:packages`
- `STAGING_DEPLOY_PATH` Environment variable

Manually dispatch `.github/workflows/deploy-staging.yml` from `main` with:
- full `source_sha`;
- exact backend `sha256:` digest;
- exact frontend `sha256:` digest.

The workflow verifies inputs and image revision labels, runs the migration service, deploys application containers, checks Docker health and attempts to restore previous images on failure. It requires a healthy previous backend and frontend.

**Important:** staging is a single-host Docker Compose deployment. It is suitable for release validation, not a proof of multi-replica zero downtime.

## 4. Production deployment gate

Do not run `scripts/deploy-production.sh` for a production cutover yet. On the inspected baseline:
- it accepts one image digest rather than distinct backend/frontend digests;
- its image existence check is only a placeholder;
- the supplied digest is not wired into the rendered deployment images;
- the external endpoint smoke test is only a placeholder;
- application and infrastructure manifests still contain digest placeholders;
- the connected Railway project is a separate ERPNext/MariaDB environment, not ERP03.

Before a production release, resolve the blockers in [the Zero-Downtime Deployment Runbook](ZERO_DOWNTIME_DEPLOYMENT_2026-11.md), including PostgreSQL HA, SQLite journal migration, connection-pool caps and actual staging failover/rollback evidence. Production runtime secrets must be provisioned outside Git.

## 5. Kubernetes rollout verification

After the production script and all stateful dependencies are qualified, deploy only with explicit production approval:

```bash
kubectl config current-context
kubectl kustomize infra/kubernetes/overlays/production >/tmp/erp03-production.yaml
# Inspect the rendered result locally; confirm no image/secret placeholders.
kubectl apply -k infra/kubernetes/overlays/production/
kubectl -n erp03 rollout status deployment/erp03-frontend --timeout=10m
kubectl -n erp03 rollout status deployment/erp03-backend --timeout=10m
kubectl -n erp03 get pods,services,endpoints,hpa,pdb
```

Confirm real endpoint health, 5xx rate, p95/p99 latency, database connections, Redis errors, migration state and audit logging. Keep the previous release available until acceptance.

## 6. Rollback

Rollback only the application Deployment that requires restoration. Record the known-good revision or immutable image digest for backend and frontend independently; do not automatically roll both back together.

Inspect history before choosing a target:

```bash
kubectl -n erp03 rollout history deployment/erp03-backend
kubectl -n erp03 rollout history deployment/erp03-frontend
```

Restore only the backend to its immediately previous revision:

```bash
./scripts/rollback.sh backend
```

Restore one Deployment to a specific recorded revision:

```bash
./scripts/rollback.sh backend --revision 12
```

Or restore only that Deployment to its exact previously verified GHCR digest:

```bash
./scripts/rollback.sh backend --image ghcr.io/nyeinpyaesone-ui/erp03-backend@sha256:<64-hex-digest>
```

Use `frontend` and the frontend image repository when only the frontend needs rollback. The script validates the selected Deployment/image pairing, captures that Deployment's rollout history, and waits for only the selected Deployment. It does not alter the other application Deployment or database schema.

Rollback is safe only while the database schema remains backward compatible. Do not automatically reverse schema migrations or restore the database as part of an application rollback.


## 7. Outstanding release blockers

- Move the SQLite transaction journal from the single ReadWriteOnce volume to a transactional shared store (prefer PostgreSQL) using a compatibility/backfill/reconciliation migration.
- Use HA PostgreSQL or a managed HA PostgreSQL service with tested restore and failover.
- Define Redis availability/security requirements and alert on fail-open throttling.
- Validate and merge the open database-pool and JWT rate-limit fixes (#275 and #274) after review and successful required checks.
- Replace every Kubernetes image digest placeholder with a verified exact digest.
- Repair and test the production deployment script before use.
- Prove rolling deployment and rollback in a staging environment that matches production topology.

A green image build is not a database recovery test or a zero-downtime proof.
