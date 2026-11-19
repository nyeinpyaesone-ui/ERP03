# ERP03 Engineering Roadmap

**Last reviewed:** 2026-11-20  
**Repository:** `nyeinpyaesone-ui/ERP03`  
**Code snapshot reviewed:** `b705086cf17f8c81286e73842a146a3be6fec9d6` on `fix/myanmar-operations-theme`  
**Architecture direction:** modular monolith; FastAPI + SQLAlchemy async + PostgreSQL; React/Vite frontend.

> This roadmap records repository evidence and work order. It is not a production-readiness certificate. Status must be refreshed against the exact commit, actual deployment environment and completed test evidence before release.

## 1. Product and engineering outcome

Deliver a dependable Myanmar-focused business ERP for day-to-day sales/POS, catalog, customers, inventory, purchasing and financial operations. Optimise useful business output—correct completed transactions, responsive operator workflows and reliable reporting—not raw request volume in isolation.

Engineering priorities, in order:

1. **Correctness and tenant isolation:** money, stock, invoice numbering, idempotency, transaction boundaries, concurrency and auditability.
2. **Reliability and recoverability:** bounded dependencies, safe migrations, backup/restore, rollback, health/readiness and failure visibility.
3. **Measured performance:** latency, throughput, query cost, lock contention, pool saturation and browser experience.
4. **Capacity and scale:** increase replicas or add async processing only after database and state-sharing limits are resolved.
5. **Evolvability:** maintain explicit module/API contracts; extract a service only where measured load, ownership or deployment independence justifies it.

Do not trade financial correctness, stock accuracy, audit trails or tenant separation for latency. Do not add caching, queues, Celery, microservices or extra infrastructure without an identified bottleneck and an acceptance test.

## 2. Current repository baseline

The reviewed source tree already contains useful performance foundations:

- React pages are lazy-loaded; Vite defines vendor/UI/utility chunks and uses OXC minification.
- Static frontend assets are configured for compression and long-lived caching through Nginx.
- Product, customer and supplier endpoints have bounded pagination (maximum page size 200).
- SQLAlchemy uses an async engine, bounded pool settings, pre-ping, recycle and checkout timeout.
- Prometheus request counters/histograms and database pool gauges exist.
- POS sale creation uses a PostgreSQL transaction, idempotency fingerprinting, row locks, stock movements and payment writes.
- Redis provides the sorted-set rate limiter; Redis failure currently trips a fail-open circuit.

These are implementation facts, not measured capacity claims. The repository does not yet provide a repeatable production-like performance qualification report.

### Material capacity and correctness constraints found

| Finding | Current evidence | Roadmap consequence |
|---|---|---|
| SQLAlchemy pool envelope | Production settings enforce at least 20 pooled + 50 overflow connections per process. Production HPA allows 3–10 backend pods. | At one worker per pod, the theoretical application pool ceiling is 70 × 10 = 700 connections. Validate and cap against PostgreSQL capacity before scaling. |
| Pool remediation proposal | PR #275, `fix/bound-db-pool-by-hpa`, is still open in the inspected GitHub state and proposes 4 + 2 per process. | Review/test/merge through the normal PR gates; do not treat the proposal as already applied. Use the formula in the performance checklist. |
| Rate-limit tenant identity | Current rate-limit middleware decodes JWT claims with signature verification disabled before using `business_id`. | Security correctness is a release prerequisite. PR #274 proposes signature/expiry verification and remains open in the inspected GitHub state. |
| SQLite transaction journal | `TransactionStore` uses SQLite WAL and process-local thread locking; Kubernetes mounts its data on a ReadWriteOnce volume. | Not safe evidence for multi-node, multi-replica transaction processing. Resolve journal storage/coordination before relying on HPA scale-out. |
| POS row-lock scope | Sale creation locks the branch, warehouse, optional customer and products; invoice allocation uses a branch lock and a `MAX(invoice_no)` query. | Profile same-branch contention before changing lock scope or invoice-number allocation. Preserve uniqueness, numbering policy and stock invariants. |
| Catalog search/pagination | List functions execute a count query and a page query; search uses contains-style `ILIKE '%term%'`; pagination uses offset. | Profile on representative tenant data before adding indexes, trigram extensions or keyset pagination. |
| Redis pool envelope | Rate-limiter Redis client defaults to 50 connections per process. | Model Redis connection use independently from PostgreSQL; 10 one-worker pods can expose a 500-connection theoretical ceiling. |
| Observability | Request count/latency and DB pool gauges exist. Query-level timings, DB lock-wait metrics and a repeatable load baseline are not established by the inspected implementation. | Instrument first; do not infer bottlenecks from request latency alone. |
| Vercel API integration | The same-origin API proxy requires `ERP03_BACKEND_ORIGIN`. The linked Vercel project had no environment variables when checked. | Preview build readiness is not successful API connectivity. Configure a verified HTTPS origin and smoke-test authenticated calls. |

The code snapshot at `b705086` produced a successful Vercel Preview build. Its Vite output reported an initial vendor chunk of 290.72 kB (92.20 kB gzip), CSS of 16.27 kB (4.07 kB gzip), and separate lazy page chunks. These are artifact-size observations, not browser LCP/INP/CLS measurements or an end-user performance result.

## 3. Delivery phases and acceptance gates

### Phase 0 — Stabilise correctness and capacity limits (P0)

- [ ] Review and qualify PR #274: verify JWT signature, expiry and required tenant claims before assigning tenant-specific rate-limit buckets. Forged, expired or incomplete tokens must fall back safely; verify regression tests.
- [ ] Review and qualify PR #275: cap per-process DB connections and test development/staging/production settings. Calculate total potential connections across the maximum pod and worker count, then reserve capacity for migrations, monitoring, backup and operator access.
- [ ] Move the SQLite journal/idempotency coordination to a shared transactional store, preferably PostgreSQL, before relying on multi-replica writes. Define a compatibility/backfill/reconciliation plan; retain a verifiable rollback path and test duplicate/replay behaviour under concurrent requests.
- [ ] Validate PostgreSQL transaction boundaries, unique constraints, row locks and tenant scoping for sales, payments and stock movements.
- [ ] Prove backup restoration and schema compatibility in a non-production environment.
- [ ] Keep production deployment blocked until stateful storage, database availability, immutable image digests, secret provisioning and rollback are proven.

**Exit gate:** no correctness/security blocker; explicit DB and Redis connection budgets; tested journal semantics under concurrent clients; restore evidence exists. Do not increase production replica count as a workaround for unresolved shared state.

### Phase 1 — Establish a repeatable performance baseline (P0/P1)

- [ ] Create deterministic synthetic datasets with tenant/branch separation and representative product, customer, invoice, invoice-line, payment and stock-balance cardinalities.
- [ ] Record the test machine, DB version/configuration, Redis config, app worker count, pod count, CPU/memory limits, dataset seed and commit SHA.
- [ ] Exercise auth/current-user, catalog page/search, inventory reads and the POS sale critical path.
- [ ] Run single-user, normal-concurrency, peak-concurrency and same-branch contention profiles. Do not run multi-replica transaction tests while the journal still depends on the single RWO SQLite file.
- [ ] Capture throughput, p50/p95/p99 latency, error rate, response size, database query count/time, lock waits/deadlocks, pool wait/saturation, Redis latency/fail-open events and CPU/memory.
- [ ] Save raw test output and a concise before/after report. Use the same data seed and environment for comparisons.

**Exit gate:** a reproducible baseline exists for each priority endpoint/workflow. Numeric service SLOs are agreed only after the baseline and expected operating load are understood.

### Phase 2 — Optimise database and transaction hot paths (P1)

- [ ] Profile the POS sale transaction by stage: validation, branch/warehouse/product locks, invoice allocation, invoice/item inserts, stock updates and payment inserts.
- [ ] Quantify same-branch contention caused by locking the branch row for invoice allocation. If it is material, design a per-branch atomic counter/allocation mechanism; preserve the approved invoice-number policy and unique constraints.
- [ ] Inspect product/stock row-lock acquisition order for multi-line sales. Keep lock ordering deterministic and test deadlock/retry behaviour.
- [ ] Measure the per-line stock lookup/update path in `adjust_stock`. Batch reads/writes only when query-count/latency evidence justifies it and stock invariants remain atomic.
- [ ] Capture `EXPLAIN (ANALYZE, BUFFERS)` for real high-volume queries using anonymised, production-like data. Add or change indexes only when the plan and write-amplification trade-off support it.
- [ ] Profile catalog count + page queries and contains-style search. Consider keyset pagination for deep pages and trigram/full-text search only where the actual search workload needs it.
- [ ] Keep one transaction boundary for invoice, payment, stock movement and idempotency outcome. Test concurrent duplicate requests, payload mismatch, overpayment and insufficient stock.
- [ ] Set connection pool size from the total connection budget, not an environment label or assumed traffic volume.

**Exit gate:** query plans and benchmark evidence show a repeatable improvement with no lost/duplicated sales, incorrect balances, negative stock, tenant leakage, or change to audit semantics.

### Phase 3 — Improve instrumentation and operator visibility (P1)

- [ ] Retain route-template labels; never use tenant IDs, user IDs, invoice IDs, raw URLs or unbounded error messages as metric labels.
- [ ] Add DB query-duration/count instrumentation with safe query fingerprints, plus pool checkout wait/timeouts and transaction duration.
- [ ] Expose lock-wait/deadlock and slow-query evidence from PostgreSQL (for example, a controlled `pg_stat_statements` rollout after assessing permissions and overhead).
- [ ] Add metrics for Redis circuit-open/fail-open events and rate-limit decisions. Do not expose Redis errors as high-cardinality labels.
- [ ] Verify whether OpenTelemetry is actually initialised and instrumented at application startup before claiming distributed trace coverage; the presence of a helper module alone is not evidence.
- [ ] Reconcile the two checked-in Prometheus rule files and their metric names; validate the exact file loaded by each deployment.
- [ ] Add dashboards for API RED metrics, DB pool/latency, Redis degradation, business transaction outcomes and frontend web vitals.
- [ ] Alert on sustained symptoms and saturation, not one-off spikes. Document owner, severity, runbook and a test for every alert.

**Exit gate:** operators can identify which layer caused a latency/error regression and correlate a business request with its logs, trace (where enabled) and DB evidence without exposing secrets or personal data.

### Phase 4 — Frontend perceived performance and output efficiency (P1/P2)

- [ ] Measure real browser experience on dashboard, sales/POS, products, customers and inventory routes, including low-powered mobile devices and constrained Myanmar network conditions.
- [ ] Capture LCP, INP, CLS, route navigation time, API wait time, JS parse/evaluation time and transferred bytes at representative viewports.
- [ ] Keep route-level lazy loading and split boundaries only where they reduce initial transfer without creating excessive request waterfalls.
- [ ] Identify unused dependencies, duplicated client code and oversized route chunks before changing packages.
- [ ] Use loading/error/empty states that distinguish slow network, authentication expiry, backend outage and empty business data.
- [ ] Avoid caching authenticated or transaction responses by default. Add client/server caching only with tenant-aware keys, explicit freshness and tested invalidation.
- [ ] Keep Myanmar fonts and text rendering in the performance test set; do not remove required language assets merely to reduce bundle size.

**Exit gate:** before/after browser measurements show an improvement on the target routes and device/network profile without broken navigation, stale financial data or accessibility regressions.

### Phase 5 — Scale only the proven bottleneck (P2/P3)

- [ ] Recalculate DB/Redis pool budgets whenever pod count or worker count changes.
- [ ] Resolve shared journal state and database capacity before multi-replica write load tests.
- [ ] Test HPA scale-up/down, pod termination, DB restart, Redis outage, migration overlap and rollback in staging.
- [ ] Consider read replicas only for read workloads with explicit consistency requirements and measured primary saturation.
- [ ] Consider background jobs/outbox workers only for work that can be retried idempotently and does not weaken synchronous financial invariants. The current backend dependency set does not establish an existing Celery worker stack.
- [ ] Extract a service only when a measured throughput, isolation or ownership requirement cannot be met within the modular monolith.

**Exit gate:** load and failure-injection reports prove that the proposed capacity change improves the limiting metric and preserves recovery/correctness under failure.

## 4. Work prioritisation

| Priority | Work item | Dependency | Done when |
|---|---|---|---|
| P0 | JWT claim verification (#274) | Independent review + CI | Forged/expired JWT cannot select another tenant's rate-limit bucket |
| P0 | DB pool cap (#275) | Connection budget + CI | Max pod × worker × pool envelope remains within allocated DB capacity |
| P0 | Shared transaction journal | Data compatibility plan | Concurrent multi-replica idempotency/replay is tested on shared transactional storage |
| P0 | PostgreSQL restore and HA plan | Runtime owner + staging | Restore/failover evidence and RPO/RTO are recorded |
| P1 | Baseline load harness | Synthetic data + staging-like environment | Repeated, comparable results with commit and environment metadata |
| P1 | Query and lock profiling | Baseline | Slow query/lock evidence for POS and catalog hot paths |
| P1 | DB/Redis observability | Metrics and dashboards | Query time, pool waits, lock waits and fail-open events are measurable |
| P1 | Frontend field/lab performance | Preview/staging and target devices | Web-vitals and route timing reports exist |
| P2 | Selective query/index changes | Query plans | Each change has an EXPLAIN and before/after result |
| P2 | Cache/read scaling | Proven read bottleneck | Tenant isolation, freshness and invalidation tests pass |
| P3 | Queue/service extraction | Proven background/service boundary | Operational cost is justified by measured throughput/ownership need |

## 5. Definition of done for a performance change

Every performance PR must state:

1. **Problem:** exact endpoint, workflow or resource that is slow/saturated, with evidence.
2. **Baseline:** commit SHA, test dataset, workload shape, environment and p50/p95/p99 or resource metrics.
3. **Hypothesis:** expected limiting factor and why the change should improve it.
4. **Correctness constraints:** money, stock, tenant, idempotency, ordering, audit and consistency invariants that must not change.
5. **Change scope:** smallest module/query/configuration change; no unrelated dependency or architecture churn.
6. **Verification:** unit/integration tests, PostgreSQL-backed concurrency test where relevant, security/tenant test, load comparison and rollback note.
7. **Result:** measured before/after values, regressions, confidence/limitations and follow-up.

If no measurable improvement is demonstrated, do not keep complexity merely because it appears faster in theory.

## 6. Source-of-truth documents

- [Performance Optimisation Checklist](PERFORMANCE_OPTIMIZATION_CHECKLIST.md) — repeatable qualification procedure and evidence template.
- [Architecture Blueprint](ARCHITECTURE_BLUEPRINT_2026-11.md) — current module/data/deployment boundaries.
- [Production Readiness Matrix](PRODUCTION_READINESS_MATRIX.md) — implementation state versus qualification evidence.
- [Zero-Downtime Deployment](ZERO_DOWNTIME_DEPLOYMENT_2026-11.md) — rollout and stateful dependency constraints.
- [Deployment Runbook](DEPLOY_RUNBOOK.md) — actual delivery/rollback commands and release gates.
- [Remediation Tracker](TODO.md) — historical implementation evidence; use this roadmap for current priority order.
- [Configuration & Credentials](../CONFIGURATION_SETUP.md) — environment and registry setup.
