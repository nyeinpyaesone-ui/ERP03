# ERP03 Zero-Downtime Deployment and Runtime Configuration

**Scope:** existing single-host staging path and Kubernetes production target  
**Repository baseline:** `main` at `716f305f` (2026-11-12)  
**Status:** deployment configuration is being hardened; production zero downtime is **not yet qualified**.

> Rolling application Deployments prevent avoidable pod-replacement gaps. They cannot make a single-instance PostgreSQL database, a ReadWriteOnce SQLite journal, or a single-host Compose staging service highly available. Do not use this runbook for production cutover until all hard gates pass.

## 1. Actual environments and delivery paths

| Environment | Checked-in delivery path | Important boundary |
|---|---|---|
| Local development | Docker Compose / devcontainer | Local-only defaults; not a production topology |
| Staging | Manual `.github/workflows/deploy-staging.yml` over SSH to a Docker Compose host | Single-host Compose; no multi-replica rollout |
| Kubernetes staging | `infra/kubernetes/overlays/staging` | Manifests exist, but the inspected staging workflow does not apply this overlay |
| Production target | `infra/kubernetes/overlays/production` and `scripts/deploy-production.sh` | Production script is not yet qualified; do not run for a cutover |

ERP03 image repositories:
- `ghcr.io/nyeinpyaesone-ui/erp03-backend`
- `ghcr.io/nyeinpyaesone-ui/erp03-frontend`

The backend and frontend publishing workflows use GitHub Actions' `GITHUB_TOKEN` with `packages: write`. Do not add a Docker Hub token for these workflows. If GHCR packages are private, provision a namespace/host-scoped read-only pull credential; otherwise verify anonymous pulls are allowed.

## 2. Existing staging workflow configuration

The manual staging workflow is triggered from `main` with:
- `source_sha`: full 40-character source commit SHA;
- `backend_digest`: published backend OCI digest;
- `frontend_digest`: published frontend OCI digest.

Configure these GitHub Environment secrets in `staging`:

| Secret | Purpose |
|---|---|
| `STAGING_SSH_PRIVATE_KEY` | Runner SSH private key |
| `STAGING_SSH_KNOWN_HOSTS` | Pinned staging host key |
| `STAGING_SSH_HOST` | Staging server hostname |
| `STAGING_SSH_USER` | Restricted deployment account |
| `STAGING_SSH_PORT` | SSH port; optional, defaults to 22 |
| `STAGING_GHCR_USERNAME` | GHCR username for the remote host |
| `STAGING_GHCR_READ_TOKEN` | Read-only GHCR token with `read:packages` |

Set the GitHub Environment variable `STAGING_DEPLOY_PATH` to the existing checkout path on the staging host. The host must contain the repository Compose file, Docker Engine, Compose plugin and a clean Git working tree.

The workflow:
1. validates full source SHA and OCI digests;
2. installs SSH credentials and enforces known-host checking;
3. authenticates the host to GHCR;
4. requires a previous running backend and frontend for rollback;
5. fetches the requested source and verifies image revision labels;
6. runs the Compose migration service;
7. replaces backend/frontend services and polls container health;
8. restores prior application images if the deployment fails.

This does not establish zero downtime: the Compose services run on one host and are not configured as multiple independent replicas behind a load balancer. It is staging deployment automation, not the Kubernetes production rollout.

## 3. Runtime secrets — keep them out of Git

The Kubernetes base Kustomization deliberately does not apply the example Secret. Provision a real `erp03-secrets` Kubernetes Secret in each namespace using an external secrets manager / External Secrets Operator, or an operator-controlled file outside the repository.

Required keys:
- `SECRET_KEY` — random signing key, at least 32 characters.
- `POSTGRES_PASSWORD` — credential for the ERP03 PostgreSQL user.
- `REDIS_PASSWORD` — credential for the internal ERP03 Redis service.

For a controlled manual bootstrap, prepare a file outside the repository with exactly those three key/value pairs, restrict it to owner read/write, and load it in the target namespace:

```bash
chmod 600 /secure/path/erp03-runtime.env
kubectl create namespace erp03 --dry-run=client -o yaml | kubectl apply -f -
kubectl -n erp03 create secret generic erp03-secrets \
  --from-env-file=/secure/path/erp03-runtime.env \
  --dry-run=client -o yaml | kubectl apply -f -
```

Repeat with namespace `erp03-staging` and staging-specific credentials. Never place runtime files under the Git checkout, commit values, paste them into CI logs, or apply `erp03-secrets.example.yaml`.

GitHub image publishing needs `GITHUB_TOKEN`; the manual staging deploy workflow requires the staging SSH and read-only GHCR secrets above. Do not place database passwords or the application signing key in GitHub Actions for this workflow. Any production cluster identity must be separately scoped and approved.

## 4. Build and pin immutable images

1. Merge the source change through review and require CI, Quality, Security, Container, Docker, Type Check, Coverage and Policy Enforcement to complete.
2. Publish backend and frontend on the intended release tag.
3. Capture the exact image digest for each image from its successful workflow summary.
4. Set each target overlay to the exact digest; do not use `latest` for production.
5. Confirm the backend/frontend digest contains both `linux/amd64` and `linux/arm64` manifests.
6. Resolve all infrastructure image digest placeholders before applying the Kubernetes base: PostgreSQL 15, Redis 7.4 and optional Ollama 0.5.4.

Useful inspection commands:

```bash
docker buildx imagetools inspect ghcr.io/nyeinpyaesone-ui/erp03-backend:<tag>
docker buildx imagetools inspect ghcr.io/nyeinpyaesone-ui/erp03-frontend:<tag>
```

Never invent or reuse a digest from an earlier build. A digest identifies exact image content, not a release label.

## 5. Pre-deployment gates

Before applying a Kubernetes overlay:

- Confirm target cluster, current context and namespace explicitly.
- Confirm the real `erp03-secrets` Secret exists in the target namespace without printing its values.
- Confirm PostgreSQL backup/restore evidence, capacity and connection limits.
- Confirm Redis authentication, network policy and rate-limiter degraded-mode alerting.
- Confirm no schema migration breaks the currently running backend.
- Resolve the SQLite journal/shared-state blocker in Section 8.
- Confirm every rendered image reference contains a real digest and no placeholder.
- Confirm ingress DNS, TLS certificate, storage class and PVC binding are available.

Render and inspect manifests:

```bash
kubectl config current-context
kubectl get namespace erp03 erp03-staging
kubectl -n erp03 get secret erp03-secrets
kubectl kustomize infra/kubernetes/overlays/staging > /tmp/erp03-staging-rendered.yaml
kubectl kustomize infra/kubernetes/overlays/production > /tmp/erp03-production-rendered.yaml
```

Do not print Secret resources to terminal output, attach rendered files with secret data to tickets, or upload them as public workflow artifacts.

## 6. Kubernetes application rollout policy

Backend and frontend Deployment templates now specify:
- `RollingUpdate`;
- `maxUnavailable: 0` and `maxSurge: 1`;
- `minReadySeconds: 10`;
- `progressDeadlineSeconds: 600`;
- `revisionHistoryLimit: 5`;
- startup, readiness and liveness probes;
- 45-second termination grace and a short preStop drain delay.

The production overlay raises each web Deployment to three replicas and patches both PDBs to `minAvailable: 2`. The backend HPA remains configured for three to ten replicas.

These are application-layer safeguards. The backend rolling strategy must not be used as proof of HA while it still depends on a single ReadWriteOnce volume for SQLite journal writes. Resolve that stateful dependency before using the production overlay.

## 7. Redis configuration and behavior

The Kubernetes Redis probes now invoke a shell and set `REDISCLI_AUTH` from the container environment; Kubernetes exec probes do not perform shell-style `$(VAR)` expansion inside a plain argument array. This avoids passing the literal string `$(REDIS_PASSWORD)` to `redis-cli` and avoids exposing the password as a CLI argument.

Redis backs distributed rate limiting, not the domain transaction ledger. The backend client now uses `REDIS_MAX_CONNECTIONS` (default/configured value 50 per process), a 2-second connect timeout, a 2-second operation timeout, a 30-second health check and graceful pool cleanup. With ten backend pods and one Uvicorn process per pod, the configured upper bound is 500 pooled connections; lower the cap if the actual Redis service plan has a smaller connection budget. The rate limiter has fail-open circuit-breaker behavior and `/api/v1/readyz` checks PostgreSQL/schema state rather than Redis. Monitor Redis timeouts, connection-pool exhaustion, memory/evictions and circuit-breaker-open events separately. The single Redis pod remains a failure domain.

## 8. Hard blockers to a zero-downtime claim

### 8.1 SQLite journal is not horizontally safe in the current deployment

`TransactionStore` uses SQLite WAL mode, thread/process-local application locking and a file under `/app/.local`. The backend Deployment mounts `erp-data-pvc` with `ReadWriteOnce`; production runs three replicas and can scale to ten. This topology does not provide a reliable shared write path across nodes.

Required remediation:
1. Implement a PostgreSQL-backed journal table with tenant-scoped unique idempotency keys and database-enforced uniqueness.
2. Use a compatibility window: create the new schema first, deploy code compatible with old and new journals, backfill and reconcile counts/fingerprints, then switch writes/reads to PostgreSQL.
3. Keep the legacy journal as a read-only rollback source until verification and the rollback window are complete.
4. Remove the SQLite PVC mount only in a later release after evidence confirms no active code path depends on it.
5. Load-test duplicate requests, concurrent claims, crash/retry and reconciliation across multiple backend pods.

Do not place SQLite WAL on a network filesystem as a shortcut for multi-replica access.

### 8.2 Database and cache service availability

The checked-in PostgreSQL StatefulSet has one replica; the Redis Deployment has one replica. Neither manifest proves automatic failover. Before claiming full-service zero downtime, use a supported managed HA PostgreSQL service or a proven HA cluster, validate failover behavior, and demonstrate point-in-time restore. For Redis, document that rate limiting fails open during outages; alert on that condition and decide whether HA Redis is required by the security policy.

### 8.3 Connection budget

The current `main` config's production auto-tuning forces a pool size of at least 20 plus 50 overflow connections per process. With ten pods this can request up to 700 application connections before migrations and operations. PR #275 proposes a 4 + 2 cap and tests, giving a theoretical maximum of 60 across ten pods. It remains an open PR in the inspected snapshot; merge only after checks and review.

### 8.4 Security and readiness

PR #274 adds JWT signature/expiry verification before tenant-specific rate-limit identity is trusted. It is also open in the inspected snapshot; complete its review and merge gate before release. Redis is deliberately not a hard readiness dependency while the rate limiter is designed to fail open. Export and alert on Redis degradation independently.

### 8.5 Production deployment script is not yet a release controller

The current `scripts/deploy-production.sh` accepts one image digest but does not inject it into the backend and frontend references. Its image-existence and external health-check steps are placeholders; the checked-in manifests still include digest placeholders for the application and infrastructure images. Do not run this script for a production cutover until it accepts and validates both application digests, renders a complete manifest with no placeholders, verifies image signatures/architecture as applicable, executes actual endpoint smoke tests, and records the known-good release.

The current `scripts/rollback.sh` uses an outdated Docker Hub namespace; it must be kept aligned with the GHCR publisher and preferably use immutable previous digests rather than mutable tags.

## 9. Database migration policy

Use expand/contract for every production schema change:
1. **Expand:** add nullable columns/tables/indexes without removing old schema.
2. **Deploy compatible code:** old and new application versions must both work against the expanded schema.
3. **Backfill:** make the operation resumable and measurable; avoid a long blocking transaction.
4. **Verify:** compare counts, key uniqueness and domain invariants.
5. **Switch:** enable the new code path behind a reversible configuration/feature flag where practical.
6. **Contract later:** drop legacy columns/tables only after the rollback window closes.

Do not run destructive migrations as an implicit side effect of starting every replica. Use one controlled migration job with database backup and lock/timeout controls.

## 10. Rollback

For a Kubernetes application rollback:

```bash
kubectl -n erp03 rollout undo deployment/erp03-backend
kubectl -n erp03 rollout undo deployment/erp03-frontend
kubectl -n erp03 rollout status deployment/erp03-backend --timeout=10m
kubectl -n erp03 rollout status deployment/erp03-frontend --timeout=10m
```

Rollback is safe only while the database schema remains backward compatible. Do not automatically reverse a migration or restore a database backup as part of an application rollback. Database restoration is a separately approved recovery operation with a defined RPO/RTO and reconciliation plan.

## 11. Qualification evidence required

Do not mark production qualified until evidence is retained for:
- staging deployment and smoke tests (recorded separately from production claims);
- a Kubernetes rollout with zero unavailable frontend/backend replicas;
- migration compatibility while old and new app versions coexist;
- PostgreSQL failover and point-in-time restore;
- transaction-journal backfill and multi-pod idempotency/load tests;
- Redis failure/circuit-breaker behavior and alert delivery;
- image digest/signature/architecture verification for app and infrastructure images;
- application rollback without schema rollback;
- ingress smoke tests during rolling replacement.

No production or Railway resource was modified as part of this repository configuration change.
