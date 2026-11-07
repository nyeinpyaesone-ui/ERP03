# ADR-001: Modular Monolith Architecture

## Context
ERP03 needed a foundation for business capabilities (authentication, inventory, sales, purchasing, catalog). The team considered splitting into microservices early versus building a modular monolith.

## Decision
Build a modular monolith: single deployable unit with business capabilities behind explicit app/domain boundaries. Add capabilities behind boundaries rather than splitting prematurely into services.

## Alternatives Considered
- Microservices from day one: higher operational complexity, network latency, distributed data consistency challenges.
- Monolith with no boundaries: coupling risk, harder to extract services later.

## Consequences
- Simpler deployment, testing, and debugging initially.
- Clear boundaries make future service extraction possible.
- Target capability sequence defined: authentication → business profile → capability registry/compiler → policy/context → runtime/workflow → approvals/audit → control tower → AI agent integration → end-to-end qualification.

## Operational Impact
- Single container image for backend, single container image for frontend.
- Shared database schema; tenant isolation via `business_id` claims.

## Migration/Rollback Implications
- No migration needed (initial architecture).
- Future service extraction would require new deployment units and API contracts.

## Status
Accepted
