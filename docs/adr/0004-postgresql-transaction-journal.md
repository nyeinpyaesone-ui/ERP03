# ADR-0004: Shared PostgreSQL Transaction Journal and Recovery State Machine

## Status

Proposed — implementation and migration qualification required.

## Context

The current `TransactionStore` persists tenant-scoped idempotency records in SQLite using WAL mode and a process-local `threading.RLock`. The API creates one store per backend process. The Kubernetes production overlay runs three backend replicas and its HPA can scale to ten, while the SQLite data path is mounted through a ReadWriteOnce PVC.

The lock does not coordinate processes or pods. A ReadWriteOnce volume does not provide a safe shared-write contract across replicas or nodes. The journal is also separate from the PostgreSQL transaction that performs authoritative ERP domain mutations. A journal row with status `accepted` is not evidence that an invoice, payment, inventory update, or other business operation committed.

Issue #222 requires recoverable cross-module orchestration, crash recovery, bounded retries, safe concurrent reconciliation, and observability.

## Decision

1. PostgreSQL is the shared durable store for production idempotency records and operation lifecycle state. It remains the authoritative database for ERP domain entities.
2. Keep the existing FastAPI modular monolith. Do not add a microservice, distributed transaction coordinator, Celery, or Redis queue solely for this problem.
3. Enforce idempotency in PostgreSQL with a unique constraint on `(business_id, idempotency_key)`. Store a canonical request fingerprint and reject a same-key/different-payload request with the existing typed conflict contract.
4. Persist operation identity, canonical command metadata, state, attempt count, retry schedule, lease ownership/expiry, timestamps, and a sanitized last-error code. Do not persist credentials or unnecessary sensitive request data.
5. Use explicit legal state transitions:
   - `accepted -> processing`
   - `processing -> committed` only in the same PostgreSQL transaction as the authoritative domain mutation
   - `processing -> retryable` for a transient failure
   - `processing -> reconciliation_required` when the outcome is ambiguous or a lease expires
   - `retryable -> processing` after its retry time
   - `reconciliation_required -> processing` after a successful lease claim
   - `processing -> failed_terminal` after a classified permanent failure or bounded retry exhaustion
6. Claim work with PostgreSQL row-level concurrency control (for example, `SELECT ... FOR UPDATE SKIP LOCKED`) and a time-bounded lease. A worker may finalize only while it owns the current lease token.
7. For domain work contained in PostgreSQL, commit the domain mutation and the journal's `committed` transition atomically in one database transaction. For external side effects, write an outbox record in that same transaction and deliver it through an idempotent consumer; do not hold a database transaction open across a network call.
8. Reconciliation uses bounded exponential backoff with jitter, a maximum-attempt policy, stale-lease recovery, and an explicit manual-review terminal path. Every handler must be idempotent at its domain boundary.
9. SQLite remains available for local development and isolated unit tests only. Production must not use a per-process SQLite journal.

## Migration and rollout

1. Add the PostgreSQL journal schema through an Alembic migration. Keep the migration additive and backward-compatible with the current application release.
2. Implement the PostgreSQL store behind the existing store contract and test it against real PostgreSQL in CI. Preserve the SQLite adapter for local tests.
3. Define and rehearse a write-fenced migration: stop journal writes, take a protected SQLite snapshot, import records, verify row counts, tenant/key uniqueness, fingerprints and deterministic sample checksums, then switch all replicas to PostgreSQL.
4. Do not dual-write two stores as an implicit consistency strategy. There is no atomic commit spanning SQLite and PostgreSQL.
5. Keep the SQLite snapshot read-only for the agreed retention/rollback window. Rollback to SQLite is allowed only before PostgreSQL accepts new writes. After cutover writes begin, recover forward from PostgreSQL; do not silently switch back and lose accepted commands.
6. Remove the SQLite PVC mount only in a later release after code-path and runtime evidence proves it is unused.

## Validation requirements

- Same tenant/key/same fingerprint returns the original operation ID.
- Same tenant/key/different fingerprint returns HTTP 409 with the existing conflict code.
- Different tenants may use the same raw idempotency key without collision.
- Concurrent requests across independent database connections and worker processes create one operation.
- Crash injection before and after domain commit never produces a false `committed` response or duplicate domain mutation.
- Ambiguous timeouts, worker lease expiry, retries, permanent failures, and retry exhaustion are tested.
- Migration tests cover legacy rows with and without fingerprints and verify counts/checksums.
- Metrics and structured logs include operation/request IDs, state transitions, retry counts, and sanitized error codes.
- PostgreSQL restore and reconciliation are exercised in staging before multi-replica production use.

## Consequences

### Positive

- Idempotency is enforced across replicas by the database, not process-local locks.
- Journal and domain outcomes can share a transaction boundary.
- Recovery is explicit, observable, and safe under concurrent workers.
- Existing API conflict semantics and modular-monolith boundaries can be retained.

### Trade-offs

- PostgreSQL becomes a hard dependency for production transaction-journal writes.
- Schema migration and legacy data import require a controlled write fence.
- Reconciliation requires operational ownership, metrics, alerts, and runbooks.
- A PostgreSQL single instance is still a failure domain; this ADR does not make the database highly available.

## Alternatives considered

- **Keep SQLite and one backend replica:** rejected as the production target because it constrains availability and horizontal scaling and leaves the journal separate from domain transactions.
- **Shared SQLite over a network filesystem:** rejected because WAL and filesystem locking semantics do not establish a reliable multi-node transactional contract.
- **Redis as the journal:** rejected because Redis is an operational rate-limiting dependency, not the authoritative durable ERP transaction store.
- **Distributed two-phase commit:** rejected as unnecessary complexity for a modular monolith sharing one PostgreSQL database.
- **A new transaction microservice or Celery queue:** rejected until measured scale or independently deployable boundaries justify the added failure modes.
