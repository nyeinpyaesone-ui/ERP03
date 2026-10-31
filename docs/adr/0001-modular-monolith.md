# ADR-0001: Modular Monolith Architecture

## Status

Accepted

## Context

ERP03 needs to support multiple business capabilities (auth, catalog, sales, inventory, etc.) while remaining deployable as a single unit. The team is small and the domain is still evolving.

## Decision

Adopt a modular monolith pattern:
- Single deployable unit (FastAPI + React/Vite)
- Business capabilities behind explicit app/domain boundaries (`app/services/`, `app/models/`, `app/api/`)
- Shared database with tenant-scoped queries (`business_id` from JWT)
- Alembic for schema migrations with single head

## Consequences

- **Positive**: Simple deployment, shared transactions, easy refactoring
- **Negative**: Scaling requires vertical scaling or future service extraction
- **Mitigation**: Clear module boundaries allow future extraction if needed

## Alternatives Considered

- Microservices: Rejected due to operational complexity for small team
- Serverless: Rejected due to stateful transaction requirements
