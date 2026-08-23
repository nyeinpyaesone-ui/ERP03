# ERP03 Integration Standardization

## Purpose

This document defines the minimum production standard for the ERP ↔ AI integration boundary. It extends the existing `INTEGRATION/` bridge without duplicating ERP business logic.

## System authority

- `ERP-BACKEND` is the system of record.
- `INTEGRATION/` owns transport contracts, compatibility, validation, authentication, and adapters.
- `AI-BACKEND` is a consumer of approved ERP capabilities.
- AI must never access ERP ORM models, repositories, database sessions, migrations, or internal services.

## Contract standard

Every integration capability MUST define:

1. Versioned endpoint or event name.
2. Explicit request and response schemas.
3. Authentication/service identity requirements.
4. Authorization performed by ERP.
5. Correlation ID propagation.
6. Idempotency behavior for commands.
7. Deterministic error codes and HTTP mapping.
8. Timeout and retry policy.
9. Compatibility/deprecation policy.
10. Contract tests.

## Command standard

Commands MUST carry a unique command/request identifier and an idempotency key where the operation can mutate ERP state. A repeated key MUST NOT create a second business transaction.

AI may request an ERP action, but ERP validates actor identity, permissions, workflow state, business rules, and transaction boundaries before committing.

## Money and ERP business rules

Currency conversion, tax, budget enforcement, approval thresholds, and accounting rules remain ERP domain responsibilities. Integration transports the required values; it does not reimplement those rules.

## Events

Approved ERP events MUST use a versioned envelope containing event ID, event type, event version, occurred-at timestamp, correlation ID, producer, and payload. Consumers must tolerate unknown fields and reject unsupported major versions safely.

## Security

- Service authentication is mandatory.
- Secrets/tokens must never be committed.
- No credentials belong in contract fixtures.
- Least-privilege service identities are required.
- Integration endpoints must reject unauthenticated and unauthorized requests.

## Qualification gate

M2 is complete only when contract tests execute successfully in CI and prove authentication, authorization, schema validation, idempotency, error semantics, and compatibility behavior against an authoritative ERP endpoint or a deterministic test double explicitly representing that endpoint.
