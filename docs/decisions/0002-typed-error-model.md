# ADR-002: Typed Error Model with Stable Machine-Readable Codes

## Context
Error handling was inconsistent across routers: some used `ValueError`, some `HTTPException` directly, and error codes were derived by sniffing error-message text (fragile).

## Decision
Introduce `AppError` base class with stable `code` attribute; subclasses for `ValidationError`, `ConflictError`, `NotFoundError`, `ForbiddenError`, `InsufficientStockError`, `SaleValidationError`, `BootstrapConflictError`, `PaymentError`. Single `AppError` handler maps to stable JSON envelope with `code`, `message`, `request_id`. `error_from_code()` provides O(1) reverse lookup.

## Alternatives Considered
- Continue message-sniffing: fragile, breaks on wording changes.
- Different error envelope per router: inconsistent client experience.

## Consequences
- Clients can rely on stable error codes.
- TypeSafe classification drives `Retry-After` header (code-owned decision).
- `IDEMPOTENCY_KEY_REUSED` vs `IDEMPOTENCY_PAYLOAD_MISMATCH` distinguished by typed code, not message content.

## Operational Impact
- Error envelope is consistent across all API endpoints.
- Security headers applied to all responses including 500s.

## Migration/Rollback Implications
- No migration needed; code-level change only.

## Status
Accepted
