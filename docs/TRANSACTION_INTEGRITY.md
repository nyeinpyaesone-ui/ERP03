# Transaction Integrity

## Implemented

- Durable SQLite transaction journal with WAL mode for local development and standalone use.
- Shared PostgreSQL transaction journal for staging and production, using the `transaction_journal` table created by Alembic revision `0010_txn_journal` (down revision: `0009_invoice_numbering_index`).
- Database-enforced tenant-scoped idempotency uniqueness in PostgreSQL on business_id and the raw idempotency key.
- Atomic SQLite BEGIN IMMEDIATE transaction boundary for the local journal.
- PostgreSQL savepoint handling for concurrent idempotency-key insert races.
- Same-key replay returns the original journal record and transaction identifier.
- Concurrent same-key requests are serialized by database uniqueness and persist exactly one journal record.
- Journal records use accepted; they are not marked committed by the journal endpoint.
- Authenticated transaction create and lookup endpoints.
- Tenant isolation derived from the verified access-token claims.
- Explicit business_id storage and indexed transaction lookup.
- Backward-compatible migration for existing SQLite journals, including recovery of tenant IDs from legacy business-scoped idempotency keys.
- Business-scoped idempotency keys.
- Durable POS sale idempotency enforced at the invoice database boundary.
- Persistent /data Docker volume for local/standalone use.
- Backend tests for required idempotency keys, replay behavior, concurrency, unauthenticated requests, tenant isolation, amount rounding, and legacy journal migration.
- CI workflow covering backend compile/tests and frontend build.

## API contract

POST /api/v1/transactions requires both Authorization: Bearer access-token and X-Idempotency-Key.

GET /api/v1/transactions/{transaction_id} also requires a bearer token. The endpoint only returns records belonging to the authenticated token's business. A record owned by another business returns the same 404 Transaction not found response as a missing record.

Request:

```json
{
  "operation": "invoice.create",
  "amount": "100.00",
  "currency": "MMK",
  "metadata": {"invoice": "INV-001"}
}
```

The idempotency key is the caller's stable operation identifier. The API scopes it to the authenticated business, so two businesses can safely use the same raw key. Repeating a key within the same business returns the original transaction. Amounts are normalized to two decimal places; positive amounts that round to zero are rejected.

## Environment-specific persistence

- Development and standalone runtime use the local SQLite journal.
- Staging and production use the PostgreSQL transaction_journal table.
- Staging/production return 503 TRANSACTION_JOURNAL_UNAVAILABLE if the configured database is not PostgreSQL. They never fall back to a pod-local SQLite file.
- The PostgreSQL table uses a composite unique constraint on business_id and the raw idempotency key. Tenant identity is not encoded into the key string.
- The local SQLite journal remains a compatibility path for development and standalone use; it is not a shared multi-replica store.

## Important transaction boundary

The journal endpoint records a durable intent with status accepted; it does not execute the operation named in the operation field. A journal row alone must not be treated as proof that an invoice, payment, or inventory mutation has occurred. Older journal rows previously labelled committed are normalized to accepted by the local store because that endpoint never performed the domain mutation. Each real business operation must update its domain records within the domain database transaction and define how journal status is reconciled with that result.

POS sale idempotency remains enforced at the PostgreSQL invoice boundary, where the sale, payments, and stock effects are coordinated.

The separate operations state machine tracks cross-module work and its reconciliation lifecycle. It does not turn an accepted journal record into a committed business transaction. Domain mutations and their authoritative operation outcome must commit in the same PostgreSQL transaction.

## Legacy SQLite journal backfill

The backfill utility is intentionally read-only by default. Run it from ERP-BACKEND after the PostgreSQL schema migration has been applied and with a frozen/read-only copy of the legacy SQLite journal:

```bash
python scripts/migrate_transaction_journal.py --source /path/to/legacy/transactions.sqlite3
```

Review the source row count, rows already present, and rows that would be inserted. To perform the import, pass the explicit --apply flag:

```bash
python scripts/migrate_transaction_journal.py --source /path/to/legacy/transactions.sqlite3 --apply
```

The target is the configured PostgreSQL DATABASE_URL. The script preserves transaction IDs, tenant IDs, payload fingerprints, metadata, and timestamps; it converts historical journal-only committed labels to accepted. Rows without a recoverable tenant ID or rows that conflict with an existing target record fail closed. Re-running the import is safe when existing records match exactly.

Migration/cutover requirements:

1. Take and retain a verified backup of the legacy journal and its containing volume.
2. Apply Alembic migrations through revision `0010_txn_journal` to the target database; it follows `0009_invoice_numbering_index`.
3. Freeze legacy journal writes and create a consistent read-only source copy.
4. Run the backfill without --apply; review counts and conflict output.
5. Run the backfill with --apply during the approved migration window.
6. Re-run in dry-run mode; it must report all source rows as already present and no conflicts.
7. Deploy the application with staging/production configured for PostgreSQL.
8. Retain the original SQLite source read-only through the agreed rollback and reconciliation window.

Do not delete the legacy SQLite file/PVC or run the backfill against a live production database without a separately approved change window. Application code changes do not constitute a completed data migration.

## Idempotency payload conflicts

For newly recorded journal entries, the store hashes a canonical JSON representation of operation, normalized amount, currency, and metadata. Repeating the same business-scoped key with the same command returns the original record. Reusing that key with a different command returns HTTP 409 with code IDEMPOTENCY_PAYLOAD_MISMATCH. Metadata object key order does not affect the fingerprint.

Legacy records migrated without a fingerprint retain backward-compatible replay behavior because their original command cannot be reliably reconstructed. Any replay of such a key returns IDEMPOTENCY_KEY_REUSED; historical fingerprints must not be invented.
