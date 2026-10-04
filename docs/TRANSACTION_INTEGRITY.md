# Transaction Integrity

## Implemented

- Durable SQLite transaction journal with WAL mode.
- Unique idempotency-key constraint.
- Atomic `BEGIN IMMEDIATE` transaction boundary.
- Same-key replay returns the original transaction identifier.
- Concurrent same-key requests are serialized and commit exactly once.
- Authenticated transaction lookup endpoint with business isolation.
- Business-scoped idempotency keys.
- Durable POS sale idempotency enforced at the invoice database boundary.
- Persistent `/data` Docker volume.
- Backend tests for required idempotency keys, replay behavior, and concurrency.
- CI workflow covering backend compile/tests and frontend build.

## API contract

`POST /api/v1/transactions` requires `X-Idempotency-Key`.

Request:

```json
{
  "operation": "invoice.create",
  "amount": "100.00",
  "currency": "MMK",
  "metadata": {"invoice": "INV-001"}
}
```

The idempotency key is the caller's stable operation identifier. Transaction and POS sale endpoints require authentication; POS idempotency is persisted in PostgreSQL and scoped to business and branch. Repeating the same key returns the original transaction instead of creating a duplicate.

## Remaining integrity work

This slice establishes the persistence/idempotency foundation. Cross-module business transactions still need domain-specific participants and compensation/recovery tests as those modules are introduced.
