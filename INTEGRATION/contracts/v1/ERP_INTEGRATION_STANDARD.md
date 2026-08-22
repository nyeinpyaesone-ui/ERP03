# ERP03 Integration Contract Standard v1

## Purpose

This document is the implementation standard for every ERP-BACKEND ↔ integration ↔ AI-BACKEND contract.

## 1. Authority

ERP-BACKEND is the system of record and the sole authority for:

- authentication context and business authorization
- validation and business rules
- workflow/state transitions
- persistence and transactions
- audit records
- idempotency outcomes

AI-BACKEND may request an operation but must never reproduce or bypass ERP business rules.

## 2. Boundary

Canonical flow:

`AI-BACKEND -> INTEGRATION/v1 -> ERP-BACKEND`

The integration layer exchanges DTOs/contracts only. It must not expose ORM entities, repositories, database sessions, migrations, or internal service objects.

## 3. Command standard

Every mutation command MUST contain:

- `command_id`: UUID identifying the logical command
- `command_type`: versioned allow-listed operation
- `requested_by`: authenticated service principal
- `correlation_id`: UUID used across logs/traces/audit
- `payload`: command-specific, schema-validated DTO
- `Idempotency-Key`: HTTP header for safe retries

Commands MUST reject unknown fields where practical and MUST reject malformed or unsupported command types deterministically.

## 4. HTTP semantics

- `200`: synchronous query/result
- `202`: command accepted for asynchronous processing
- `400`: invalid contract/payload
- `401`: missing or invalid service authentication
- `403`: authenticated but not authorized
- `404`: ERP resource not found
- `409`: idempotency/state/business conflict
- `422`: only when the ERP API explicitly uses semantic validation errors
- `5xx`: transient infrastructure/service failure

A `202` response MUST NOT claim that an ERP mutation has already completed.

## 5. Idempotency

The same idempotency key and equivalent command payload MUST return the original outcome without creating a second mutation.

Reuse of an idempotency key with a different payload MUST return `409`.

Retries are permitted only with the same idempotency key and command identity.

## 6. Authentication and authorization

Service authentication uses short-lived signed bearer credentials. The integration boundary validates issuer, audience, signature, lifetime, and required identity claims.

Authentication does not grant ERP business permission. ERP authorization remains mandatory for every command.

Credentials and tokens MUST never be committed or logged.

## 7. Observability

Every request/command should preserve:

`correlation_id -> command_id -> audit/event identifiers`

Sensitive credentials and secrets MUST NOT appear in logs.

## 8. Versioning

Breaking contract changes require a new major version (`v2`). Additive backward-compatible changes may remain within the current major version and must be documented.

Event consumers must tolerate unknown fields and reject unsupported major event versions.

## 9. Qualification gate

A contract is not considered production-qualified until CI demonstrates:

1. schema validation
2. authentication failure handling
3. authorization failure handling
4. not-found handling
5. idempotent duplicate handling
6. conflicting idempotency handling
7. deterministic invalid-command handling
8. actual ERP integration-route execution
9. correlation/observability propagation

Documentation alone cannot close an M2 qualification gate.
