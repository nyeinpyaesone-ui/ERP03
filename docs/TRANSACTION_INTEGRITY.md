# Transaction Integrity

## Storage and execution boundaries

- **PostgreSQL shared environments:** the transaction API stores accepted commands in the existing `operations` table through `OperationService`. Tenant-scoped uniqueness is enforced by the unique `operation_id` constraint. The key format is `{business_uuid}:{client_idempotency_key}`.
- **Local development and isolated tests:** the existing SQLite `TransactionStore` remains available as a local adapter. It is not the production multi-replica store.
- **ERP domain data:** PostgreSQL remains authoritative for invoices, payments, stock balances, stock movements, customers, suppliers and other domain entities.
- **Redis:** rate limiting only; it is not the transaction ledger.

The PostgreSQL operations table already provides the durable six-state lifecycle: `pending`, `processing`, `committed`, `failed`, `reconciliation_required` and `cancelled`. The API exposes `pending` as `accepted` for compatibility. Only a domain handler may set `committed`, and it must update the operation row in the same PostgreSQL transaction as the authoritative domain mutation.

## API contract

`POST /api/v1/transactions` requires both `Authorization: Bearer <access-token>` and `X-Idempotency-Key`.

`GET /api/v1/transactions/{transaction_id}` also requires a bearer token. PostgreSQL lookups are constrained by both operation UUID and the verified `business_id`; a foreign tenant receives the same `404 Transaction not found` response as a missing operation.

Request:

```json
{
  "operation": "invoice.create",
  "amount": "100.00",
  "currency": "MMK",
  "metadata": {"invoice": "INV-001"}
}
```

The API normalizes amounts to two decimal places and currency codes to uppercase. Positive amounts that round to zero are rejected. Repeating a business-scoped key with the same operation type and canonical payload returns the original operation ID. Reusing it with a different type, branch, tenant or payload returns HTTP 409.

The endpoint accepts an operation; it does **not** execute the named domain operation. A `201` response with `status=accepted` is not evidence that an invoice, payment, inventory update or other business action occurred.

## Worker leases and fencing

Migration `0010_operation_claim_leases` adds `claim_token` and `lease_expires_at` to the operations table and expands `operation_type` to 100 characters to match the API contract.

- Workers claim rows with a PostgreSQL row lock and `SKIP LOCKED`.
- Every claim receives a unique random token and a bounded lease.
- Workers may renew only an unexpired lease they still own.
- Commit and fail transitions use conditional SQL updates matching operation ID, worker ID, claim token, state and non-expired lease.
- A reclaimed operation receives a new token; an older worker cannot commit or fail it.
- Reconciliation returns expired claims to `pending`; rows from the pre-lease schema are recovered using the configured stale-age cutoff.
- Retry delays use exponential backoff capped at one hour. Retry exhaustion moves the operation to `reconciliation_required`.

Domain handlers must call `commit_operation` in the same database session transaction as their business changes. External side effects must be delivered through an outbox or an independently idempotent integration; do not hold a database transaction open across a network call.

## Integrated ERP domain handlers

The feature branch now wires the existing orchestration lifecycle into the two stock-changing ERP workflows:

- **POS sales — `POST /api/v1/sales`:** the sale service creates/claims a tenant-scoped `pos.sale` operation. Invoice header, invoice items, payment rows, inventory movements, stock balances and the operation `committed` result are persisted in the same PostgreSQL transaction. A retry with the same sale fingerprint returns the existing invoice without decrementing stock again; a changed request under the same key returns HTTP 409.
- **Purchase receiving — `POST /api/v1/purchases/receipts`:** requires `X-Idempotency-Key`. The operation row, stock-in movements, stock balances, weighted-average product costs and committed result are persisted in one PostgreSQL transaction. A replay returns the prior receipt totals without increasing stock a second time; a changed payload conflicts.
- **Catalog:** product/customer/supplier creation now verifies that the target branch is active and belongs to the authenticated tenant. Branch-scoped list and product-activation routes constrain access to the branch in the verified token.
- **Request unit of work:** `get_db_session` commits once after a successful request and rolls back on exceptions/cancellation. This closes a previous gap where CRUD/receiving helpers flushed changes but the request dependency closed the session without committing.

The generic `POST /api/v1/transactions` endpoint intentionally remains an acceptance API. It records intent but does not execute arbitrary operation names. POS and purchase endpoints are the domain handlers that execute their own validated work and atomically advance the corresponding operation. Other domain actions must follow the same rule before they are considered fully orchestrated.

## SQLite journal migration

The import utility is `scripts/migrate_transaction_journal.py`.

1. Put the legacy SQLite writer behind a write fence and confirm no old API replica can accept journal writes.
2. Take a consistent SQLite backup/snapshot. Keep its WAL-consistent contents read-only.
3. Apply Alembic migrations through `0010_operation_claim_leases` to the target PostgreSQL database.
4. Run the importer without `--apply` first. It validates tenant UUIDs, target Business rows, payloads, operation-key conflicts and legacy identifiers; it reports a normalized source-row checksum.
5. Compare source row counts, checksum and conflict report with the approved migration record.
6. Run with `--apply` only after the dry-run review and explicit migration approval.
7. Verify PostgreSQL row counts, tenant/key uniqueness and representative operation payloads before routing traffic to the PostgreSQL-backed API.
8. Retain the SQLite snapshot read-only for the agreed rollback window. Once PostgreSQL accepts new writes, recover forward from PostgreSQL; switching back to the old snapshot would lose new accepted commands.

Example dry-run:

```bash
cd ERP-BACKEND
DATABASE_URL="$ERP03_POSTGRES_ASYNC_URL" \
  python ../scripts/migrate_transaction_journal.py \
  --sqlite-path /secure/backups/erp03-transactions.sqlite3
```

The importer is read-only by default. Its `--apply` option writes to PostgreSQL and must be run as a controlled migration, not by application startup or every backend replica. The legacy database is never modified by this utility.

## Tests and operational evidence

The backend test suite covers SQLite idempotency behavior and the orchestration service. The feature branch adds test definitions for PostgreSQL-mode API intake against the shared operations table, request-session commit/rollback, replay/conflict behavior, POS invoice/stock atomicity, purchase receipt replay, branch isolation, claim leases, renewal, expiry recovery, stale-worker fencing, importer validation and failure-message redaction.

A test definition is not a passing test result. Run the backend test and migration workflows on this exact branch and retain their execution evidence before calling this implementation qualified.

## Remaining release gates

- Run Alembic upgrade/downgrade validation on both supported test dialects.
- Run concurrency and crash-window tests against real PostgreSQL with independent connections/processes.
- Exercise write-fenced import and reconciliation in staging using a protected snapshot.
- Extend the atomic operation pattern to any future ERP write endpoints; generic transaction intake is still acceptance-only.
- Verify PostgreSQL HA, backup/PITR and restore; the current single StatefulSet is not HA.
- Complete the staging rollback, auth, tenant-isolation and ERP workflow smoke tests before production approval.

Production readiness remains **NOT QUALIFIED** until these operational gates are evidenced.
