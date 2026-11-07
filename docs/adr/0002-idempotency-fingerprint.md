# ADR-0002: Idempotency Fingerprint Strategy

## Status

Accepted

## Context

POS sales must be idempotent to prevent duplicate charges on network retries. The system needs to distinguish between "same request replayed" and "different request with same key."

## Decision

Use SHA-256 canonical JSON fingerprint:
- Fingerprint = SHA-256(canonical JSON of sale command)
- Key format: `{business_id}:{client_idempotency_key}`
- Legacy rows without fingerprint → `IDEMPOTENCY_KEY_REUSED` (safe default)
- Conflict codes: `IDEMPOTENCY_PAYLOAD_MISMATCH` | `IDEMPOTENCY_KEY_REUSED`

## Consequences

- **Positive**: Deterministic, tamper-evident, prevents replay attacks
- **Negative**: Requires canonical serialization (sorted keys, consistent types)
- **Mitigation**: Pydantic schema validation ensures consistent input

## Alternatives Considered

- Client-provided idempotency key only: Rejected — cannot detect payload changes
- Database unique constraint only: Rejected — doesn't distinguish replay vs conflict
