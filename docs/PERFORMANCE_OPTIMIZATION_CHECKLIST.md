# ERP03 Performance Optimisation Checklist

**Version:** 1.0  
**Last reviewed:** 2026-11-20  
**Applies to:** FastAPI/SQLAlchemy/PostgreSQL/Redis backend and React/Vite frontend.

Use this checklist for each performance investigation or optimisation PR. It is a qualification workflow, not permission to tune production or relax correctness/security constraints.

## A. Scope and baseline lock

- [ ] Record repository, branch, full commit SHA and working-tree state.
- [ ] Name the target journey/API route and user-visible symptom.
- [ ] State whether the goal is lower latency, higher transaction throughput, lower resource consumption, more predictable tail latency or better browser responsiveness.
- [ ] Record the deployment topology: pods, workers per pod, CPU/memory requests and limits, DB/Redis instance size, network path and region.
- [ ] Record PostgreSQL and Redis versions/configuration, connection limits and migration state.
- [ ] Use synthetic/anonymised data; do not copy production credentials or personal/customer data into benchmark fixtures.
- [ ] Fix and record dataset seed and cardinalities per tenant/branch.
- [ ] Repeat each comparable test at least three times and retain the raw output.

**Minimum workload set**

| Workflow | Workload variation | What to capture |
|---|---|---|
| Login / current user | cold and warm request; valid and expired token | p50/p95/p99, auth CPU/time, error rate |
| Product/customer/supplier lists | first page, later page, empty search, common search, no-result search | query count/time, rows scanned, response size, p95 |
| Inventory read | one product, one warehouse, larger result set | query count/time, row count, p95 |
| POS sale | single-line and multi-line; paid/partial; new and replayed idempotency key | end-to-end time, DB time, transaction time, lock wait, result correctness |
| Concurrent POS | same branch and separate branches; same product and different products | throughput, lock wait, deadlocks, conflicts, stock correctness |
| Mixed traffic | read-heavy and write-heavy profiles | throughput, p95/p99, errors, DB/Redis saturation |
| Frontend routes | dashboard, sales, products, customers, inventory | LCP, INP, CLS, route transition, JS/CSS bytes and API wait |

Do not set an arbitrary user count and call it “production load”. Derive concurrency and data volume from the expected number of tenants, branches, tills, operators and peak operating periods. Record assumptions and owner approval.

## B. Required correctness gates

- [ ] Every read/write remains scoped to the authenticated tenant and permitted branch.
- [ ] A sale creates exactly one invoice for one idempotency key and matching payload.
- [ ] Replaying the same command returns the same committed result.
- [ ] Reusing a key with a different payload fails deterministically.
- [ ] Payment total cannot exceed the sale total.
- [ ] Stock never becomes negative under concurrent sale requests.
- [ ] Invoice number uniqueness and the approved numbering policy are preserved.
- [ ] Invoice, invoice items, payments and stock movements commit or roll back atomically.
- [ ] Audit records and request correlation survive error paths.
- [ ] PostgreSQL-backed tests are used for PostgreSQL locking, constraints and query plans; SQLite tests are not treated as equivalent evidence.
- [ ] Expected 4xx/429 responses are distinguished from unexpected 5xx responses.

Any correctness failure rejects the performance change, regardless of latency improvement.

## C. Backend and database investigation

### Connection capacity

- [ ] Calculate the maximum PostgreSQL connection envelope:

  `max_pods × workers_per_pod × (pool_size + max_overflow)`

- [ ] Add separately budgeted connections for migrations, backup/restore, metrics/exporters, monitoring and operator access.
- [ ] Compare the total with the actual PostgreSQL `max_connections` and the service's safe memory budget.
- [ ] Calculate Redis client connections separately; do not assume the PostgreSQL pool cap also constrains Redis.
- [ ] Verify pool checkout timeout, pre-ping, recycle and shutdown disposal.
- [ ] Load-test saturation and record pool wait/timeouts rather than only the idle/active gauges.
- [ ] Do not enable the 10-pod HPA while the SQLite journal remains a shared-state blocker.

Current source warning: `ERP-BACKEND/app/core/config.py` raises production pool settings to at least 20 + 50 per process. At 10 pods and one worker per pod this is a theoretical 700 PostgreSQL connection ceiling. PR #275 proposes 4 + 2 but was still open in the reviewed GitHub state. Re-check the code and PR status before using either number as current runtime configuration.

### Query and transaction profiling

- [ ] Record SQL query count and duration by safe query fingerprint.
- [ ] Capture representative PostgreSQL `EXPLAIN (ANALYZE, BUFFERS)` plans.
- [ ] Check index scans, rows scanned/returned, sort/hash spills, sequential scans, buffer hit/read ratio and planning/execution time.
- [ ] Check table/index bloat and stale statistics before attributing all latency to application code.
- [ ] Measure transaction duration, row-lock wait, deadlock count and retry count.
- [ ] Inspect the POS path: branch/warehouse/customer/product locks, invoice-number allocation, stock balance reads/writes and payment inserts.
- [ ] Measure the serialisation caused by locking the branch row during invoice allocation.
- [ ] Keep row-lock acquisition deterministic for multi-product operations; prove the change with concurrent PostgreSQL tests.
- [ ] Measure per-line stock updates before attempting batch operations.
- [ ] Inspect catalogue count + page queries and contains-style `ILIKE` searches on representative tenant sizes.
- [ ] Add/alter indexes only with query-plan evidence and migration/write-cost review.
- [ ] Consider keyset pagination only after validating client navigation/sort semantics and stable cursor ordering.
- [ ] Never remove a tenant predicate, uniqueness constraint, transaction boundary or lock solely to improve a benchmark.

### Redis and operational dependencies

- [ ] Measure Redis command latency, pool usage, connection errors and rate-limit decisions.
- [ ] Emit a bounded metric for circuit-open/fail-open events; existing warning logs alone are not an operator dashboard.
- [ ] Test rate limiting with valid, expired, malformed and forged tokens.
- [ ] Verify rate limiter identity before using tenant claims; do not trust unsigned JWT payloads.
- [ ] Decide explicitly whether a Redis outage should fail open or fail closed for each use. Current rate limiting intentionally fails open; business writes must still be protected by database invariants.
- [ ] Do not add a cache for sales, payments, stock or balances without an explicit consistency/invalidation contract.

## D. Frontend and network investigation

- [ ] Capture baseline bundle output from the production build and compare route chunks.
- [ ] Measure real browser LCP, INP and CLS on target devices and network conditions.
- [ ] Measure API time separately from frontend render/hydration/JS evaluation time.
- [ ] Check request waterfalls, duplicate calls, unnecessary payload fields and unbounded list responses.
- [ ] Keep route-level lazy loading where it lowers initial route cost.
- [ ] Review chunk splitting against actual dependency graphs; avoid too many tiny chunks or repeated vendor code.
- [ ] Use compression and immutable cache headers only for hashed static assets.
- [ ] Do not cache authenticated API responses or financial data by default.
- [ ] Keep accessible loading, error, offline and empty states.
- [ ] Include Myanmar Unicode/font rendering and low-bandwidth device/network cases.

## E. Observability and performance regression checks

- [ ] Confirm request metrics use stable route templates and bounded labels.
- [ ] Add query duration/count, pool checkout wait, transaction duration, lock wait and Redis circuit metrics.
- [ ] Correlate logs with a request ID; redact tokens, credentials, payment references and personal data.
- [ ] Confirm OpenTelemetry is initialised and exported before claiming trace coverage.
- [ ] Reconcile Prometheus rule files and make sure the deployed Prometheus config loads the intended rule file.
- [ ] Add tested alerts for sustained high p95/p99, elevated 5xx, pool saturation, DB lock/deadlock pressure and Redis fail-open.
- [ ] Define dashboard panels and alert owner/runbook links.
- [ ] Check CPU throttling, memory pressure, restarts and event-loop lag during the same workload.
- [ ] Compare before/after runs using identical data, topology and traffic shape.

## F. Safe optimisation acceptance

- [ ] The PR identifies the baseline and a specific measured bottleneck.
- [ ] The change is the smallest viable intervention.
- [ ] At least three repeatable before/after runs are retained.
- [ ] The target metric improves beyond normal run-to-run variation.
- [ ] p99, error rate, correctness, DB saturation and other critical metrics do not materially regress.
- [ ] The test covers normal, peak and contention cases relevant to the change.
- [ ] Migrations are reversible or have an explicit forward-recovery procedure.
- [ ] Rollback is documented and does not reverse financial data or schema unsafely.
- [ ] CI, security, policy, type, coverage and integration gates pass for the exact commit.
- [ ] Independent review is complete before merge.
- [ ] The evidence and final decision are added to the PR and remediation tracker.

## G. Change evidence template

Copy this block into the PR description:

```text
Target workflow/route:
Observed symptom:
Baseline commit:
Environment/topology:
Dataset seed and size:
Concurrency / request mix:
Baseline p50 / p95 / p99:
Baseline throughput:
Baseline errors / correctness checks:
Database query count and time:
Pool / lock / Redis saturation:
Hypothesis:
Smallest change:
Correctness tests:
After p50 / p95 / p99:
After throughput:
After errors / correctness checks:
After resource consumption:
Repeat count and run links:
Known trade-offs:
Rollback plan:
Decision: ACCEPT / REJECT / NEEDS MORE EVIDENCE
```

## H. Current investigation queue

- [ ] Qualify PR #274 JWT verification before tenant-specific rate-limit bucketing.
- [ ] Qualify PR #275 connection-pool cap against real PostgreSQL connection capacity.
- [ ] Resolve SQLite journal's multi-replica storage/coordination limitation.
- [ ] Build repeatable PostgreSQL-backed POS/catalog load scenarios.
- [ ] Instrument DB query latency/count, pool wait and lock contention.
- [ ] Profile branch-level invoice allocation and multi-line stock updates.
- [ ] Audit catalog `ILIKE` and offset-pagination query plans.
- [ ] Measure real browser web vitals; existing bundle output is not a substitute.
- [ ] Reconcile Prometheus rules and verify alert loading/operation.

For priority order and phase exit gates, see [Engineering Roadmap](ROADMAP.md).
