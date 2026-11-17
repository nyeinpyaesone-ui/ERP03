# ERP03 Architecture Reconciliation and Implementation Plan

**Baseline:** `main` at `9a2a234061f7deef5d65150c271e0647c1983598`  
**Working branch:** `feat/erp03-architecture-reconciliation`  
**Assessment date:** 2026-11-18  
**Production status:** NOT QUALIFIED

This plan maps the implementation checklist to the existing ERP03 architecture. It extends existing workflows and modules; it does not create duplicate pipelines or invent an unselected cloud-provider topology.

## Phase 0 — reconcile source evidence

- [x] Confirm current repository tree, default branch and baseline SHA.
- [x] Confirm backend (FastAPI), frontend (React/Vite), PostgreSQL, Redis, SQLite journal, Kustomize overlays, Terraform contract, and existing delivery workflows.
- [x] Identify active PRs and avoid duplicating PR #274 (JWT claim verification), #275 (database pool cap), #289 (readiness evidence audit), and #290 (workflow/preflight hardening).
- [x] Record the current transaction-journal and deployment constraints in ADR-0004.
- [ ] Merge/reconcile the readiness audit after its source SHA and evidence are refreshed to the then-current main.

## P0 — release and correctness gates

1. **GitHub Actions startup failures**
   - Diagnose Policy Enforcement and Infrastructure Validation at the check-suite/run-service layer.
   - Current main SHA `9a2a234061f7deef5d65150c271e0647c1983598` has Policy Enforcement run #296 ending `startup_failure`; zero jobs were created.
   - Do not weaken OPA rules, mark the check successful, or replace it with a skipped check.
   - Capture current-SHA evidence for every required workflow once the platform issue is resolved.

2. **Review existing security and connection-pool changes**
   - Independently review PR #274 before relying on verified JWT claims for tenant rate-limit buckets.
   - Independently review PR #275 and validate the aggregate pool budget against actual PostgreSQL `max_connections`, migrations, admin sessions and all worker processes.
   - Do not copy these open PRs into this branch or claim their changes are on main.

3. **Deployment artifact integrity**
   - Keep production deployment blocked while Kustomize contains `REPLACE_WITH_REAL_*_DIGEST` values.
   - Resolve each image only from successful trusted GHCR build/publish evidence; verify platform manifests, signature and source-revision metadata.
   - Repair and test the production deploy contract before any production rollout. The current deployment script is not qualified to prove or apply both selected backend/frontend digests.

## P1 — transaction integrity

<text>Source implementation staged on this feature branch:</text>

- [x] Route PostgreSQL transaction intake through the existing shared `operations` table; retain SQLite only for local/dev and isolated tests.
- [x] Add Alembic revision `0010_operation_claim_leases` with fenced claim tokens, lease expiry, scan index and an expanded operation type.
- [x] Add operation-specific lease claims, renewal, commit/fail fencing, stale-lease recovery and bounded retry handling.
- [x] Add read-only-by-default SQLite journal import tooling with tenant/key/UUID validation and a write-fenced `--apply` mode.
- [x] Make POS sale invoice, payment, stock and operation outcome atomic; retries replay the existing invoice without duplicate stock movement.
- [x] Make purchase receiving, stock-in, weighted-average cost and operation outcome atomic; require a tenant-scoped idempotency key.
- [x] Fix request-scoped SQLAlchemy unit-of-work commit/rollback behavior.
- [x] Enforce branch ownership and branch-scoped catalog access.
- [x] Add test definitions for replay, fencing, import validation, request commit/rollback, POS, purchase receipts and branch isolation.

**Not yet validated:** this branch has not had its backend test suite, Alembic migration, cross-process PostgreSQL concurrency, importer against a protected snapshot, or staging recovery drills executed. No test pass or production qualification is claimed.

## P1 — stateful infrastructure and recovery

- Decide managed HA PostgreSQL versus a supported PostgreSQL HA operator; do not describe the current single StatefulSet/PVC as HA.
- Define approved RPO/RTO, encrypted off-host backups, retention, PITR/WAL handling, restore ownership and recurring isolated restore drills.
- Keep Redis dedicated to rate limiting. Define availability/fail-open alerts, connection budget, authentication, TLS and recovery expectations.
- Do not reuse the separate Railway ERPNext/MariaDB/Redis project as ERP03 infrastructure without a separately approved compatibility/migration plan.

## P1 — Kubernetes and release engineering

- Render dev, staging and production overlays in CI and assert namespace transformations, Secret references, PVC bindings, service selectors, resource limits and probes.
- Replace placeholder digests only with verified immutable artifacts; keep GHCR publisher names aligned with overlay image sources.
- Keep staging's current SSH + single-host Docker Compose workflow distinct from the Kubernetes staging overlay.
- Require exact source SHA and backend/frontend digests, signature/revision verification, controlled migrations, readiness checks, functional smoke tests and rollback evidence.
- Treat the current production deploy script and canary placeholder as blocked until their real verification/deployment behavior is tested.

## P2 — platform and observability

- Select cloud/provider, region, network CIDRs, compute, database/cache services and remote Terraform state before implementing provider-specific infrastructure modules.
- Keep Terraform validation and plan-only CI separate from any apply; apply requires explicit environment approval.
- Verify Prometheus target discovery, Grafana dashboard provisioning, Alertmanager delivery and alerts for API errors/latency/saturation, DB pool exhaustion, Redis degradation, journal retry backlog and reconciliation age.
- Add frontend lint/type-check only after selecting the repository's preferred tools and confirming existing scripts.
- Keep AI/TypeSafe integration optional and outside authoritative ERP transaction decisions.

## Production acceptance gate

Production may be considered only when all of the following are evidenced on the exact release candidate:

- Required CI, security, container and policy jobs are created and pass.
- Production overlays render without placeholders and use verified immutable digests.
- Staging uses those exact digests and passes auth, tenant-isolation, POS/purchase atomicity, rate-limit, observability and smoke tests.
- Journal migration, concurrent idempotency, crash recovery and reconciliation tests pass.
- PostgreSQL backup/restore, failover/RPO/RTO and rollback drills are recorded.
- Runtime secrets, TLS, ingress, network policy and monitoring/alert delivery are verified.
- Deployment rollback is rehearsed and the exact artifact can be promoted without rebuilding.

No production deployment, infrastructure apply, database migration, secret mutation or main-branch merge is authorized by this plan.
