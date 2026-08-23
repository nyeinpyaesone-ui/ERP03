# ERP03 Integration Contract v1

## Boundary

`AI-BACKEND -> INTEGRATION -> ERP-BACKEND`

The integration layer is the only supported communication boundary. AI code must not import ERP ORM models, repositories, database sessions, migrations, or internal business services.

## Contract rules

- All endpoints are versioned under `/integration/v1`.
- Service-to-service authentication is mandatory.
- Commands require an `Idempotency-Key` and a unique `command_id`.
- ERP remains the authority for authorization, validation, business rules, state transitions, audit, and persistence.
- AI may request approved operations but cannot execute ERP business logic itself.
- Contract payloads contain primitives/DTOs only; ORM entities are prohibited.
- Unknown required command types are rejected with `400`.
- Authentication failures return `401`; authorization failures return `403`.
- Duplicate idempotency keys must not create a second ERP mutation; return the original result or `409` for conflicting payload reuse.
- Retries are safe only for requests carrying the same idempotency key.
- Client timeout: 5 seconds for query requests; 10 seconds for command acceptance.
- Client retry: maximum 3 attempts with exponential backoff and jitter; never retry `400`, `401`, `403`, or deterministic `409` conflicts.

## Event envelope

Future approved ERP events use these fields:

```json
{
  "event_id": "uuid",
  "event_type": "erp.purchase_order.approved",
  "event_version": 1,
  "occurred_at": "RFC-3339 timestamp",
  "correlation_id": "uuid",
  "source": "erp-backend",
  "data": {}
}
```

Consumers must ignore unknown fields and reject unsupported major event versions.
