# ADR-0004: PostgreSQL Operations as the Shared Transaction Journal

## Status

Proposed — staged implementation on `feat/erp03-architecture-reconciliation`; review and staging qualification are still required.

## Context

The inspected `main` baseline routes `POST /api/v1/transactions` to `TransactionStore`, which persists idempotency records in SQLite using WAL mode and a process-local `threading.RLock`. The API creates one store per backend process. The Kubernetes production overlay runs three backend replicas and its HPA can scale to ten, while the SQLite data path is mounted through a ReadWriteOnce PVC.

The lock does not coordinate processes or pods. A ReadWriteOnce volume does not provide a safe shared-write contract across replicas or nodes. The journal is also separate from the PostgreSQL transaction that performs authoritative ERP domain mutations. An accepted journal row is not evidence that an invoice, payment, inventory update or other business operation committed.

ERP03 already has a PostgreSQL-backed `operations` table and `OperationService` with tenant identity, canonical command payloads, six lifecycle states, row-locking claims, retries and reconciliation. Adding a second journal table would duplicate this state model.

## Decision

1. Reuse the existing PostgreSQL `operations` table as the shared production operation journal. Do not add a second journal table or a distributed transaction coordinator.
2. Route transaction intake to `OperationService` whenever `DATABASE_URL` uses PostgreSQL. Retain the SQLite `TransactionStore` only for local development and isolated tests.
3. Namespace caller idempotency keys as `{business_uuid}:{client_idempotency_key}` in the unique `operations.operation_id` column. A matching tenant, operation type, branch context and canonical payload replays the existing operation; a different command conflicts.
4. Preserve the API distinction between acceptance and execution: the API maps `pending` to `accepted`. It does not execute a generic operation. A domain handler may mark an operation `committed` only in the same PostgreSQL transaction as the authoritative domain mutation.
5. Keep the existing lifecycle states: `pending`, `processing`, `committed`, `failed`, `reconciliation_required` and `cancelled`. Retryable failures use `failed` plus `backoff_until`; bounded retry exhaustion moves to `reconciliation_required`.
6. Fence worker ownership with a random `claim_token` and `lease_expires_at`. Claims use PostgreSQL row locking with `SELECT ... FOR UPDATE SKIP LOCKED`. Renew, commit and fail operations must conditionally match the current worker, token, state and unexpired lease.
7. Stale leases return to `pending` for safe re-claiming. A worker whose token has been replaced must never commit or fail the operation.
8. Store only a safe generic error summary and a bounded error code in the operation record. Raw exception text may contain credentials or personal data and must not be persisted.
9. For domain work contained in PostgreSQL, commit the domain mutation and operation's `committed` transition atomically in one session transaction. External side effects require an outbox or independently idempotent consumer; do not hold a database transaction open across a network call.
10. SQLite is never the shared production journal. Redis remains a rate-limiting dependency, not the transaction ledger.

## Migration and rollout

1. Apply Alembic revision `0010_operation_claim_leases`, which adds claim-token and lease-expiry columns, an index for lease scans, and expands `operation_type` to 100 characters to match the API contract.
2. Put all legacy SQLite journal writers behind a write fence and take a consistent SQLite backup/snapshot.
3. Run `scripts/migrate_transaction_journal.py` in dry-run mode. It validates tenant UUIDs and Business rows, preserves legacy transaction UUIDs, checks operation-key collisions and prints a normalized-row checksum.
4. Review source counts, checksum, tenant/key uniqueness and conflicts. Run with `--apply` only as a controlled, explicitly approved migration. The importer never modifies its SQLite source.
5. Legacy rows import as `pending`, never `committed`, because the SQLite journal recorded acceptance but did not prove that a PostgreSQL domain mutation committed.
6. Verify imported row counts, IDs, tenant ownership and payloads before switching backend replicas to the PostgreSQL intake path.
7. Keep the SQLite snapshot read-only for the agreed rollback window. After PostgreSQL accepts new writes, recover forward from PostgreSQL; switching back to the old snapshot would lose accepted commands.
8. Remove the SQLite PVC mount only in a later reviewed release after runtime evidence proves it is unused.

There is no dual-write mode: no atomic transaction spans SQLite and PostgreSQL.

## Validation requirements

- Same tenant/key/same operation type and canonical payload returns the original operation UUID.
- Same tenant/key with a changed operation type, recorded branch or payload returns HTTP 409.
- Different tenants may use the same raw idempotency key without collision.
- PostgreSQL requests use the shared `operations` table; local SQLite mode remains supported.
- Concurrent requests over independent PostgreSQL connections/processes create one operation.
- Commit/fail updates from an expired or superseded worker token affect zero rows and return a conflict.
- Lease renewal works only for the current unexpired owner.
- Retry backoff, retry exhaustion, stale-lease recovery and manual reconciliation states are covered.
- Importer tests prove read-only source access, tenant/key normalization, UUID preservation and rejection of invalid legacy identity.
- Crash-window tests prove that domain writes and `committed` state are atomic for each real domain handler.
- PostgreSQL migration/import and restore/reconciliation are rehearsed in staging before multi-replica production use.

## Consequences

### Positive

- Production idempotency is shared across API replicas through PostgreSQL.
- The existing orchestration model is reused instead of introducing duplicate infrastructure.
- Claim tokens fence stale workers from overwriting newer work.
- Legacy SQLite data can be imported with deterministic identity preservation and a write-fenced process.

### Trade-offs

- PostgreSQL becomes a hard dependency for production transaction intake.
- A controlled snapshot import and verification window are required.
- Generic transaction intake still requires domain handlers to execute real ERP work; accepting an operation is not executing it.
- Reconciliation, metrics, alerts and operator ownership remain required.
- The current single PostgreSQL StatefulSet is still a failure domain; this ADR does not make the database highly available.

## Alternatives considered

- **Add a second PostgreSQL journal table:** rejected because the existing `operations` table already provides durable command identity and lifecycle state.
- **Keep SQLite and one backend replica:** rejected as the production target because it constrains availability and horizontal scaling.
- **Shared SQLite over a network filesystem:** rejected because WAL and filesystem locking do not establish a reliable multi-node transactional contract.
- **Redis as the journal:** rejected because Redis is an operational rate-limiting dependency, not the authoritative ERP transaction store.
- **Distributed two-phase commit or a transaction microservice:** rejected as unnecessary complexity for a modular monolith sharing one PostgreSQL database.
