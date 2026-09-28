# Transaction Integrity

## Implemented

- Durable SQLite transaction journal with WAL mode.
- Unique idempotency-key constraint.
- Atomic `BEGIN IMMEDIATE` transaction boundary.
- Same-key replay returns the original transaction identifier.
- Concurrent same-key requests are serialized and commit exactly once.
- Transaction lookup endpoint.
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

The idempotency key is the caller's stable operation identifier. Repeating the same key returns the original transaction instead of creating a duplicate.

## Remaining integrity work

This slice establishes the persistence/idempotency foundation. Cross-module business transactions still need domain-specific participants and compensation/recovery tests as those modules are introduced.
