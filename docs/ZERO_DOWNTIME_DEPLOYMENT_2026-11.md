# ERP03 Zero-Downtime Deployment and Runtime Configuration

**Scope:** Kubernetes-based ERP03 release path  
**Repository baseline:** `main` at `716f305f` (2026-11-12)  
**Status:** rollout configuration is being hardened; production zero downtime is **not yet qualified**.

> A Kubernetes rolling Deployment prevents avoidable application-pod replacement gaps. It cannot make a single-instance PostgreSQL database, a ReadWriteOnce SQLite journal, or an unverified ingress/storage setup highly available. Do not use this runbook to perform a production cutover until every hard gate below passes.

## 1. Resource and environment model

| Environment | Kubernetes namespace | Image source |
|---|---|---|
| Development | `erp03` (dev overlay) | GHCR backend/frontend |
| Staging | `erp03-staging` | GHCR backend/frontend |
| Production | `erp03` | GHCR backend/frontend, pinned by digest |

Image repositories:
- `ghcr.io/nyeinpyaesone-ui/erp03-backend`
- `ghcr.io/nyeinpyaesone-ui/erp03-frontend`

The backend and frontend publishing workflows use GitHub Actions' `GITHUB_TOKEN` with `packages: write`. Do not add a Docker Hub token for these workflows. If GHCR packages are private, provision an image pull secret in each target namespace and reference it from the pod specs; otherwise confirm package visibility permits cluster pulls.

## 2. Runtime secrets — keep them out of Git

The base Kustomization deliberately does not apply the example Secret. Provision a real `erp03-secrets` Kubernetes Secret in each environment using an external secrets manager / External Secrets Operator, or an operator-controlled file outside the repository.

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

Repeat with namespace `erp03-staging` and staging-specific credentials. Never place the runtime file under the Git checkout, commit its values, paste them into CI logs, or apply `erp03-secrets.example.yaml`. Rotate credentials only through an agreed staged procedure with both old and new credentials accepted during the overlap period where the service supports it.

GitHub Actions publishing does not require repository-level `DOCKERHUB_TOKEN`, `POSTGRES_PASSWORD`, `DATABASE_URL` or `SECRET_KEY` secrets. The image publisher uses `GITHUB_TOKEN`. A future Kubernetes deploy workflow would need its own narrowly scoped cluster identity and environment approvals.

## 3. Build and pin immutable images

1. Merge the source change through review and require CI, Quality, Security, Container, Docker, Type Check, Coverage and Policy Enforcement to complete.
2. Publish backend and frontend on the intended release tag.
3. Capture the exact image digest for each image from its successful workflow summary.
4. Replace the production overlay's two `REPLACE_WITH_REAL_*_DIGEST` placeholders with the exact digests. Do not use `latest` for production.
5. Confirm the digest has both `linux/amd64` and `linux/arm64` manifests before rollout.

Useful inspection commands:

```bash
docker buildx imagetools inspect ghcr.io/nyeinpyaesone-ui/erp03-backend:<tag>
docker buildx imagetools inspect ghcr.io/nyeinpyaesone-ui/erp03-frontend:<tag>
```

Never invent or copy a digest from an earlier build. A digest identifies exact image content, not a release label.

## 4. Pre-deployment gates

Before applying any overlay:

- Confirm the target cluster, context and namespace explicitly.
- Confirm the real `erp03-secrets` Secret exists and has all required keys without printing its values.
- Confirm PostgreSQL backup and restore evidence, database capacity and connection limits.
- Confirm Redis authentication, network policy and rate-limiter degraded-mode alerting.
- Confirm no schema migration breaks the currently running backend.
- Confirm the SQLite journal migration / shared-state blocker in Section 7 has been resolved.
- Confirm the rendered manifests contain no placeholder image digests or placeholder credentials.

Render and inspect manifests:

```bash
kubectl config current-context
kubectl get namespace erp03 erp03-staging
kubectl -n erp03 get secret erp03-secrets
kubectl kustomize infra/kubernetes/overlays/staging > /tmp/erp03-staging-rendered.yaml
kubectl kustomize infra/kubernetes/overlays/production > /tmp/erp03-production-rendered.yaml
```

Do not print Secret resources to terminal output, attach rendered files with secret data to tickets, or upload them as public workflow artifacts.

## 5. Application rollout policy

Backend and frontend Deployment templates are configured for:
- `RollingUpdate`
- `maxUnavailable: 0`
- `maxSurge: 1`
- `minReadySeconds: 10`
- `progressDeadlineSeconds: 600`
- `revisionHistoryLimit: 5`
- startup, readiness and liveness probes
- 45-second termination grace and a short preStop drain delay

The production overlay raises each web Deployment to three replicas and patches both PDBs to `minAvailable: 2`. The backend HPA remains configured for three to ten replicas.

These are application-layer safeguards. The backend rolling strategy must not be used as proof of HA while the backend still depends on a single ReadWriteOnce volume for SQLite journal writes. Resolve that stateful dependency before using the production overlay.

## 6. Safe deployment and verification sequence

After staging validation and approval:

```bash
# Staging first
kubectl apply -k infra/kubernetes/overlays/staging/
kubectl -n erp03-staging rollout status deployment/erp03-frontend --timeout=10m
kubectl -n erp03-staging rollout status deployment/erp03-backend --timeout=10m
kubectl -n erp03-staging get pods,services,endpoints

# Smoke tests (replace host with the actual staging hostname)
curl --fail https://<staging-host>/api/v1/healthz
curl --fail https://<staging-host>/api/v1/readyz
curl --fail https://<staging-host>/

# Production only after release approval and all hard gates
kubectl apply -k infra/kubernetes/overlays/production/
kubectl -n erp03 rollout status deployment/erp03-frontend --timeout=10m
kubectl -n erp03 rollout status deployment/erp03-backend --timeout=10m
kubectl -n erp03 get pods,services,endpoints
kubectl -n erp03 get hpa,pdb
```

Monitor request rate, 5xx ratio, p95/p99 latency, SQL pool checked-out/overflow, Postgres connections, Redis timeouts and circuit-breaker-open events. Verify the old ReplicaSet is scaled down only after the new pods are Ready and smoke tests pass.

## 7. Hard blockers to a zero-downtime claim

### 7.1 SQLite journal is not horizontally safe in the current deployment

`TransactionStore` uses SQLite WAL mode, thread-local process locking and a file under `/app/.local`. The backend Deployment mounts `erp-data-pvc` with `ReadWriteOnce`; production runs three replicas and can scale to ten. This storage topology does not provide a reliable shared write path across nodes.

Required remediation:
1. Implement a PostgreSQL-backed journal table with tenant-scoped unique idempotency keys and database-enforced uniqueness.
2. Use a compatibility window: create new schema first, deploy code that can read existing journal state, backfill and reconcile counts/fingerprints, then switch writes/reads to PostgreSQL.
3. Keep the legacy journal as a read-only rollback source until verification and rollback window are complete.
4. Remove the SQLite PVC mount only in a later release after evidence confirms no active code path depends on it.
5. Load-test duplicate requests, concurrent claims, crash/retry and reconciliation across multiple backend pods.

Do not place SQLite WAL on a network filesystem as a shortcut for multi-replica access.

### 7.2 Database and cache service availability

The checked-in PostgreSQL StatefulSet has one replica; the Redis Deployment has one replica. Neither manifest proves automatic failover. Before claiming full-service zero downtime, use a supported managed HA PostgreSQL service or a proven HA cluster, validate failover behavior, and demonstrate point-in-time restore. For Redis, document that rate limiting fails open during outages; alert on that condition and decide whether HA Redis is required by the security policy.

### 7.3 Connection budget

The current `main` config's production auto-tuning forces a pool size of at least 20 plus 50 overflow connections per process. With ten pods this can request up to 700 application connections before migrations and operations. PR #275 proposes a 4 + 2 cap and tests, giving a theoretical maximum of 60 across ten pods. It remains an open PR in the inspected snapshot; merge only after checks and review.

### 7.4 Security and readiness

PR #274 adds JWT signature/expiry verification before tenant-specific rate-limit identity is trusted. It is also open in the inspected snapshot; complete its review and merge gate before release. The backend readiness route validates PostgreSQL connectivity and Alembic schema state; Redis is deliberately not a hard readiness dependency while the rate limiter is designed to fail open. Export and alert on Redis degradation independently.

## 8. Database migration policy

Use expand/contract for every production schema change:
1. **Expand:** add nullable columns/tables/indexes without removing old schema.
2. **Deploy compatible code:** old and new application versions must both work against the expanded schema.
3. **Backfill:** make the operation resumable and measurable; avoid a long blocking transaction.
4. **Verify:** compare counts, key uniqueness and domain invariants.
5. **Switch:** enable the new code path behind a reversible configuration/feature flag where practical.
6. **Contract later:** drop legacy columns/tables only after the rollback window closes.

Do not run destructive migrations as an implicit side effect of starting every replica. Use one controlled migration job, with database backup and lock/timeout controls.

## 9. Rollback

Application rollback:
```bash
kubectl -n erp03 rollout undo deployment/erp03-backend
kubectl -n erp03 rollout undo deployment/erp03-frontend
kubectl -n erp03 rollout status deployment/erp03-backend --timeout=10m
kubectl -n erp03 rollout status deployment/erp03-frontend --timeout=10m
```

Rollback is safe only while the database schema remains backward compatible. Do not automatically reverse a migration or restore a database backup as part of an application rollback. Database restoration is a separately approved recovery operation with a defined RPO/RTO and reconciliation plan.

## 10. Qualification evidence required

Do not mark production qualified until evidence is retained for:
- staging rollout with zero unavailable frontend/backend replicas;
- migration compatibility while old and new app versions coexist;
- PostgreSQL failover and point-in-time restore;
- transaction-journal backfill and multi-pod idempotency/load tests;
- Redis failure/circuit-breaker behavior and alert delivery;
- image digest/signature/architecture verification;
- application rollback without schema rollback;
- ingress smoke tests during rolling replacement.

No production or Railway resource was modified as part of this repository configuration change.
