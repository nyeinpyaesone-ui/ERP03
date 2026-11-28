# ERP03 Architecture Blueprint — November 2026

**Repository:** `nyeinpyaesone-ui/ERP03`  
**Baseline inspected:** `main` at `716f305f27739c6f53dceac77126734795f2efa7` (2026-11-12)  
**Assessment date:** 2026-11-16  
**Architecture:** modular monolith; one FastAPI application and one React/Vite frontend.

> This document describes repository configuration inspected on the date above. It is not a production deployment certification. Runtime availability, database recovery and zero-downtime cutover require environment-specific evidence.

## 1. Runtime architecture

```text
Users / Browsers
      |
      | HTTPS
      v
Ingress / TLS (Kubernetes target topology)
      |
      +------------------------------+
      |                              |
      v                              v
React 19 / Vite frontend        FastAPI backend
Nginx unprivileged              Python 3.12 / Uvicorn
      |                              |
      | /api                         +-------------------------+
      +----------------------------->|                         |
                                     v                         v
                              PostgreSQL 15               Redis 7.4
                              SQLAlchemy async            Sorted-set rate limits
                              Alembic migrations          Circuit-breaker fallback
                                     |
                                     v
                              SQLite transaction journal
                              Accepted-command/idempotency
                              metadata; not domain ledger
```

The Kubernetes base contains backend, frontend, PostgreSQL, Redis, Ollama, Services, Ingress, PVCs, NetworkPolicies, RBAC and probes. Dev, staging and production Kustomize overlays provide environment-specific image tags and replica settings. Docker Compose supports local and single-host runtime environments.

## 2. Application boundaries

| Layer | Repository responsibility |
|---|---|
| `ERP-BACKEND/app/api/` | HTTP contracts and routing: auth, catalog, sales, purchasing, transactions, health |
| `ERP-BACKEND/app/schemas/` | Request/response schemas |
| `ERP-BACKEND/app/services/` | Domain rules, inventory, orchestration, RBAC and bootstrap |
| `ERP-BACKEND/app/models/` | SQLAlchemy identity, ERP and operations models |
| `ERP-BACKEND/app/db/` | Async SQLAlchemy engine and session factory |
| `ERP-BACKEND/app/core/` | Configuration, errors, JWT/security, audit, metrics, TypeSafe integration and transaction journal |
| `frontend/src/` | React application and API client |
| `infra/kubernetes/` | Kubernetes base resources and dev/staging/production overlays |

Keep ERP03 as a modular monolith until measured load, deployment independence or team boundaries justify extraction. Do not introduce a Redis queue/Celery worker merely because Redis exists: the inspected backend requirements do not establish a current Celery worker architecture.

## 3. Current pinned technology evidence

| Component | Current repository evidence |
|---|---|
| Python runtime | 3.12.13 slim in backend Dockerfile |
| FastAPI | 0.162.0 |
| Uvicorn | 0.54.0 |
| SQLAlchemy | 2.1.8 with asyncio |
| Redis Python client | 8.1.0 |
| PostgreSQL driver | asyncpg 0.32.0 |
| Frontend | React / React DOM 19.3.1 |
| Vite | 8.3.6 |
| Frontend build | Node 22 Alpine |
| Frontend runtime | unprivileged Nginx 1.27 Alpine |
| Database migrations | Alembic 1.20.1 |
| Kubernetes database | PostgreSQL 15 image in base manifest |
| Kubernetes cache | Redis 7.4 Alpine image in base manifest |
| Optional AI runtime | Ollama 0.5.4 image in base manifest |

The image publishing workflows are separate:
- `.github/workflows/docker-publish.yml` builds `ghcr.io/nyeinpyaesone-ui/erp03-backend`.
- `.github/workflows/container.yml` builds `ghcr.io/nyeinpyaesone-ui/erp03-frontend`.

Both build Linux AMD64 and ARM64 images. Backend publishing includes SBOM/provenance and keyless Cosign signing/verification; frontend publishing includes SBOM/provenance and architecture verification.

## 4. Data ownership and state

| Store | Intended responsibility | Operational constraint |
|---|---|---|
| PostgreSQL | Authoritative ERP domain data and relational transactions | Current Kubernetes base is a single PostgreSQL StatefulSet/PVC, not a failover cluster |
| Redis | Distributed sliding-window rate limiting | Current Kubernetes base is one Redis pod/PVC; rate-limiter circuit breaker fails open when Redis is unavailable |
| SQLite journal | Durable transaction-intent / idempotency journal | Mounted through one ReadWriteOnce PVC on the backend Deployment; this is not safe evidence for multi-node multi-replica operation |

The rate-limiter Redis client now uses the configured per-process connection cap (`REDIS_MAX_CONNECTIONS`, default 50), 2-second connect/operation timeouts, a 30-second health check and graceful pool cleanup. With ten backend pods and one Uvicorn process per pod, the configured upper bound is 500 Redis connections; size this against the actual Redis service plan and lower it when necessary.

The SQLite journal is particularly important: `TransactionStore` uses SQLite WAL mode and per-process thread locking. The production overlay runs three backend replicas and the HPA can scale to ten. A single ReadWriteOnce PVC does not establish safe cross-node access or high availability. Do not claim that increasing backend replicas makes the journal highly available.

## 5. Deployment topology currently checked in

| Component | Base / production setting |
|---|---|
| Backend | Base 2 replicas; production overlay 3; HPA min 3 / max 10 |
| Frontend | Base 2 replicas; production overlay 3 |
| PostgreSQL | Single StatefulSet replica and 10Gi persistent volume claim |
| Redis | Single Deployment replica and 2Gi persistent volume claim |
| Ollama | Optional service manifest, single replica and 20Gi persistent volume claim |
| Ingress | NGINX ingress with TLS host placeholder `erp.example.com` |
| Health checks | Backend liveness `/api/v1/healthz`; readiness `/api/v1/readyz`; frontend HTTP probe |
| Container registry | GHCR for ERP03 backend/frontend images |

Backend and frontend Deployment templates now specify rolling update controls (`maxUnavailable: 0`, `maxSurge: 1`), readiness delay and graceful termination. The production overlay sets three web replicas and PDB minimum availability of two.

The Kubernetes PostgreSQL, Redis and Ollama base image references still contain digest placeholders. The production web image overlay also contains placeholders. Replace every such placeholder with a registry-verified digest before applying any environment that uses those resources.

## 6. CI, release and deployment paths

Current CI includes backend tests, frontend build, quality, security, container, type-check, coverage, agent-parity and policy gates.

Two image workflows publish GHCR artifacts:
- Backend: `.github/workflows/docker-publish.yml`
- Frontend: `.github/workflows/container.yml`

The manual `.github/workflows/deploy-staging.yml` workflow accepts a source SHA and two image digests, connects to a remote host over SSH, runs the migration service through Docker Compose, replaces the backend/frontend containers, checks health and attempts to restore prior images on failure. Its deployment target is a single-host Compose environment—not the Kubernetes staging overlay and not an HA deployment.

The repository has a Kubernetes production overlay and `scripts/deploy-production.sh`, but the current script does not actually verify the supplied image digest, its image existence and endpoint health steps are placeholders, and the manifests still have digest placeholders. Do not use it for a production cutover until it is repaired and validated.

At the inspected baseline, PRs #274 and #275 are open:
- #274 verifies JWT signatures and expiry before trusting tenant identity for rate limiting.
- #275 reduces SQLAlchemy per-process pool sizing for the 10-pod HPA envelope.

Their latest inspected PR heads had success for CI, Quality, Security, Container, Docker, Type Check, Coverage, Agent Parity and Devcontainer Build & Push. Historical note: the former Policy Enforcement workflow was subsequently retired from this branch; the Kubernetes Rego source files remain preserved.

## 7. External platform resource boundary

The connected Railway account exposed a project named `erpnext`, containing a Frappe/ERPNext service, MariaDB 10.6 and two Redis 6.2 services in Singapore. All those services reported offline at inspection time. Those resources are not the ERP03 repository deployment and must not be reused as ERP03's PostgreSQL or Redis dependencies without a separate explicit migration and compatibility plan.

## 8. Production-readiness blockers

1. **SQLite journal and single RWO PVC:** migrate the journal to a shared transactional store (preferably PostgreSQL) with a compatibility/backfill plan before relying on backend replicas across nodes.
2. **PostgreSQL availability:** the current single StatefulSet does not provide database failover. Use a managed HA PostgreSQL offering or a proven PostgreSQL HA operator, with tested backups and point-in-time recovery.
3. **Redis availability:** the current single pod is not HA. For rate limiting, define acceptable fail-open behavior, monitor it, and decide whether managed Redis/Sentinel/cluster failover is warranted.
4. **Pool sizing:** validate and merge PR #275 before enabling the 10-replica HPA; its proposed 4 + 2 cap keeps the theoretical application pool at 60 connections for ten pods.
5. **Security:** validate and merge PR #274 before release.
6. **Registry and digest correctness:** ensure GHCR package visibility/pull permissions and replace every web and infrastructure image digest placeholder with registry evidence.
7. **Secrets:** real runtime credentials must be created outside the repository. The placeholder secret file is retained only as a non-applied example.
8. **Staging evidence:** execute restore, rollback, migration-compatibility, load and failure-injection drills. A green unit test does not prove zero downtime.

## 9. Architecture rules

- PostgreSQL is the source of truth for ERP business entities and transactional invariants.
- Redis is an operational dependency for distributed throttling, not the accounting ledger or a substitute for database transactions.
- Keep writes tenant-scoped, idempotent and auditable.
- Prefer database constraints/transactions and explicit row locking for business correctness.
- Do not make cache/Redis availability a hard health dependency while the application intentionally fails open; alert on degraded throttling separately.
- Keep AI/TypeSafe integrations optional and outside authoritative transaction decisions.
- Extract services only after measurable need and stable contracts.

## Related operations guide

See [Zero-Downtime Deployment and Runtime Configuration](ZERO_DOWNTIME_DEPLOYMENT_2026-11.md) for staging deployment inputs, secret provisioning, digest pinning, rollout verification and the conditions that must be met before a zero-downtime claim is valid.
