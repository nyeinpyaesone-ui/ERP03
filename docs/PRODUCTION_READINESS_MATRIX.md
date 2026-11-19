# ERP03 Production Readiness Matrix

**Last reviewed:** 2026-11-20  
**Source-code evidence snapshot:** `fix/myanmar-operations-theme` at `b705086cf17f8c81286e73842a146a3be6fec9d6`  
**Scope:** repository configuration and connected Vercel project inspection. This is not a live production certification.

> Documentation commits made after the source-code snapshot require their own exact-commit CI re-run. Runtime and infrastructure claims must be refreshed against the environment being released.

## Status definitions

- **Implemented:** source/configuration exists; runtime qualification can still be pending.
- **Partial:** some parts or environments are verified; acceptance remains incomplete.
- **Evidence pending:** workflow/runtime evidence has not completed for the exact commit.
- **Blocked:** a known safety, capacity or external dependency prevents progression.
- **Unmeasured:** no repeatable performance baseline exists.
- **Not qualified:** required production acceptance evidence is incomplete.

## Current evidence matrix

| Area | Repository / platform evidence | State |
|---|---|---|
| Architecture | FastAPI + SQLAlchemy async backend and React/Vite frontend are organised as a modular monolith. | Implemented |
| Frontend route shell | Nested routes, lazy page loading, responsive layout and Myanmar theme changes exist in PR #273. | Implemented; PR review pending |
| Frontend build | Exact source snapshot `b705086`: Vercel Preview build completed; CI frontend build and proxy syntax check passed. | Partial; browser experience not measured |
| Vercel API routing | `api/[...path].js` proxies same-origin `/api/*` to FastAPI `/api/v1/*` and requires `ERP03_BACKEND_ORIGIN`. Linked `erp-03` Vercel project returned zero configured environment variables. | Blocked on verified backend origin and smoke test |
| Backend CI | Exact snapshot `b705086`: backend compile, migration and test steps completed successfully. | Passed for that SHA only |
| Quality / type / Docker | Exact snapshot `b705086`: Quality, Type Check and Docker workflows completed successfully. | Passed for that SHA only |
| Agent Parity / Coverage / Container / Devcontainer | At the last inspection of `b705086`, some jobs were still running or had not created jobs. Do not infer completion from queued/in-progress runs. | Evidence pending |
| Policy Enforcement | Latest run for `b705086` ended `startup_failure` with zero jobs. No policy job executed. | Blocked; not a pass |
| JWT rate-limit identity | Current branch middleware decodes JWT claims with signature verification disabled before using `business_id`. PR #274 proposes verification but remains open in the inspected GitHub state. | Blocked; security fix and review required |
| PostgreSQL pool sizing | Current production settings enforce at least 20 + 50 connections per process. At HPA maximum 10 pods and one worker per pod, theoretical application ceiling is 700 connections. PR #275 proposes 4 + 2 and remains open in the inspected GitHub state. | Blocked; budget and fix required |
| Redis pool sizing | Redis client allows up to 50 connections per process; 10 one-worker pods could expose a 500-connection theoretical ceiling. | Partial; capacity budget/monitoring required |
| Transaction journal | SQLite WAL with process-local locking is mounted via a ReadWriteOnce volume in the backend deployment. This is not safe evidence for cross-node multi-replica writes. | Blocked before horizontal write scaling |
| PostgreSQL / Redis availability | Checked-in Kubernetes resources use single PostgreSQL and Redis instances; no failover drill evidence was supplied by the inspected repo state. | Not qualified for HA |
| POS correctness | Sale service uses a single DB transaction, idempotency fingerprint, row locks, stock adjustments and payment inserts. Concurrent PostgreSQL stress and failure-injection results are not established by source inspection alone. | Partial |
| Query performance | Catalog paths use count + offset page queries and contains-style `ILIKE`; POS uses branch-level locking and per-line stock adjustment. No repeatable query/load report exists. | Unmeasured |
| Observability | Request counters/histograms and DB pool gauges exist. Query timing, checkout wait, lock waits and Redis fail-open metrics are not established. Two Prometheus rule files use differing metric names; active rule loading needs reconciliation. | Partial |
| Frontend performance | Vite output at `b705086`: vendor 290.72 kB / 92.20 kB gzip; CSS 16.27 kB / 4.07 kB gzip; page chunks are split. No browser LCP/INP/CLS results exist. | Partial; field performance unmeasured |
| Backups / restore | Backup, verification and restore scripts/runbooks exist. A current environment restore drill with measured RPO/RTO is not evidenced here. | Partial |
| Production deployment | Production script/manifests still have documented digest/endpoint placeholders; stateful journal and single-instance DB/cache blockers remain. | Not qualified |

## Exact-commit workflow snapshot

The workflow results below refer only to the source commit `b705086cf17f8c81286e73842a146a3be6fec9d6`, not to later documentation commits:

| Workflow | Last observed conclusion |
|---|---|
| CI (backend + frontend) | `success` |
| Quality | `success` |
| Type Check | `success` |
| Docker | `success` |
| Policy Enforcement | `startup_failure`, zero jobs |
| Agent Parity | `in_progress` |
| Container | `in_progress` |
| Devcontainer Build & Push | `in_progress` |
| Coverage | `pending` / no job created at inspection |

The Vercel Preview for that exact commit was `READY` at [erp-03 Preview](https://erp-03-92r3sxbgz-anynoob.vercel.app). A READY static deployment does not prove API connectivity: the linked Vercel project's environment-variable listing was empty, and the API origin had not been configured or smoke-tested.

## Required release gates

1. Re-run every required workflow for the exact proposed merge SHA. Policy Enforcement must create a real job and complete successfully; `startup_failure` with zero jobs is never a pass.
2. Resolve and review the JWT claim-verification issue (PR #274) before relying on tenant-derived rate-limit buckets.
3. Resolve and review the DB pool cap (PR #275) against actual PostgreSQL connection capacity, worker count, HPA and reserved operations connections.
4. Migrate or redesign the SQLite transaction journal so multi-replica writes use shared transactional coordination; prove idempotency/replay under concurrent PostgreSQL clients.
5. Set `ERP03_BACKEND_ORIGIN` in the intended Vercel environments to the verified FastAPI HTTPS origin; run health, login, token-persistence and authenticated API smoke tests.
6. Validate GHCR login/push and AMD64/ARM64 manifest verification on a push/release workflow. PR-event build steps with login/push/manifest verification skipped do not prove publication.
7. Run representative load, lock-contention, failure-injection, backup/restore and rollback drills in staging.
8. Obtain independent PR approval and verify branch protection/required checks. Do not bypass failed, skipped or missing gates.

## Current priority links

- [Engineering Roadmap](ROADMAP.md)
- [Performance Optimisation Checklist](PERFORMANCE_OPTIMIZATION_CHECKLIST.md)
- [Documentation Guidelines](DOCUMENTATION_GUIDELINES.md)
- [Architecture Blueprint](ARCHITECTURE_BLUEPRINT_2026-11.md)
- [Zero-Downtime Deployment](ZERO_DOWNTIME_DEPLOYMENT_2026-11.md)
- [Deployment Runbook](DEPLOY_RUNBOOK.md)

**Overall status: NOT QUALIFIED for production cutover or a zero-downtime claim.**