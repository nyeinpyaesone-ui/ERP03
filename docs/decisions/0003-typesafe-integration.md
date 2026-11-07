# ADR-003: TypeSafe System One Integration (Optional, Degradable)

## Context
The team wanted programmable common sense for error classification, transaction risk scoring, and idempotency conflict judgment without coupling business logic to an external AI service.

## Decision
Integrate TypeSafe as an optional, degradable layer: gated by `TYPESAFE_ENABLED` + `TYPESAFE_API_KEY`; all calls wrapped in exception handlers returning `None` on failure; code owns retry/routing/escalate decisions; model only annotates.

## Alternatives Considered
- Make TypeSafe mandatory: production outage risk if service unavailable.
- No AI integration: lose programmable common sense for error routing and risk scoring.

## Consequences
- Graceful degradation: API works identically with or without TypeSafe.
- Confidence thresholds: act >= 0.70, escalate < 0.40.
- `unclassified` choice option prevents forced misclassification.
- Client lifecycle bound to FastAPI `lifespan` shutdown.

## Operational Impact
- `TYPESAFE_ENABLED=false` by default; opt-in via environment.
- No credentials in source control; `SecretStr` field.

## Migration/Rollback Implications
- Disable by setting `TYPESAFE_ENABLED=false`.

## Status
Accepted
