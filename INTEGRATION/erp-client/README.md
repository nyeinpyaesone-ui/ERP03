# ERP Client Adapter

The ERP client is the only integration component allowed to call ERP-BACKEND.

## Rules

- Calls use only versioned integration contracts.
- No direct database connection.
- No import of ERP ORM models/repositories/services.
- Validate response envelopes before exposing data to AI-BACKEND.
- Propagate `correlation_id` and `Idempotency-Key` where applicable.
- Apply the v1 timeout/retry policy from `INTEGRATION/contracts/v1/README.md`.
- Never retry a mutation without the original idempotency key.
