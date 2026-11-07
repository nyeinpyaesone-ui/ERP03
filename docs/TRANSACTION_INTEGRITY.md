# Transaction Integrity

## Implemented

- Durable SQLite transaction journal with WAL mode.
- Unique idempotency-key constraint.
- Atomic \`BEGIN IMMEDIATE\` transaction boundary.
- Same-key replay returns the original transaction identifier.
- Concurrent same-key requests are serialized and commit exactly once.
- Authenticated transaction create and lookup endpoints.
- Tenant isolation derived from the verified access-token claims.
- Explicit \`business_id\` storage and indexed transaction lookup.
- Backward-compatible migration for existing journals, including recovery of tenant IDs from legacy business-scoped idempotency keys.
- Business-scoped idempotency keys.
- Durable POS sale idempotency enforced at the invoice database boundary.
- Persistent \`/data\` Docker volume.
- Backend tests for required idempotency keys, replay behavior, concurrency, unauthenticated requests, tenant isolation, amount rounding, and legacy journal migration.
- CI workflow covering backend compile/tests and frontend build.

## API contract

\`POST /api/v1/transactions\` requires both \`Authorization: Bearer <access-token>\` and \`X-Idempotency-Key\`.

\`GET /api/v1/transactions/{transaction_id}\` also requires a bearer token. The endpoint only returns records belonging to the authenticated token's business. A record owned by another business returns the same \`404 Transaction not found\` response as a missing record.

Request:

\`\`\`json
{
  "operation": "invoice.create",
  "amount": "100.00",
  "currency": "MMK",
  "metadata": {"invoice": "INV-001"}
}
\`\`\`

The idempotency key is the caller's stable operation identifier. The API scopes it to the authenticated business, so two businesses can safely use the same raw key. Repeating a key within the same business returns the original transaction. Amounts are normalized to two decimal places; positive amounts that round to zero are rejected.

## Important transaction boundary

The SQLite endpoint records a durable journal entry; it does **not** execute the operation named in the \`operation\` field. A journal row alone must not be treated as proof that an invoice, payment, or inventory mutation has occurred. Each real business operation must update its domain records within the domain database transaction and define how journal status is reconciled with that result.

POS sale idempotency remains enforced at the PostgreSQL invoice boundary, where the sale, payments, and stock effects are coordinated.

## Remaining integrity work

This slice establishes the persistence/idempotency foundation. Cross-module business transactions still need domain-specific participants and compensation/recovery tests as those modules are introduced.


## Idempotency payload conflicts

For newly recorded journal entries, the store hashes a canonical JSON representation of operation, normalized amount, currency, and metadata. Repeating the same business-scoped key with the same command returns the original record. Reusing that key with a different command returns HTTP 409 with code \`IDEMPOTENCY_KEY_REUSED\`. Metadata object key order does not affect the fingerprint.

Legacy records migrated without a fingerprint retain backward-compatible replay behavior because their original command cannot be reliably reconstructed. They should be upgraded through a deliberate backfill if historical payloads are available.
