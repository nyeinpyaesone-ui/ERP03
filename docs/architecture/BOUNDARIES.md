# ERP / AI Architecture Boundaries

## Target structure

```text
PROJECT/
├── ERP-BACKEND/       # System of Record
├── AI-BACKEND/        # AI / Agent System
├── INTEGRATION/       # Contract and service bridge
├── INFRASTRUCTURE/    # Runtime/platform dependencies
└── docs/              # Architecture and operational documentation
```

## Dependency rule

```text
ERP-BACKEND  <── INTEGRATION ──>  AI-BACKEND
     │                                  │
     └── database                       └── models/tools/memory
```

The ERP system remains authoritative for transactional truth. AI is a consumer/orchestrator and must not become a second system of record.

## Transitional legacy area

`backend/` is the current deployed FastAPI application. It remains temporarily because `docker-compose.yml` currently builds `./backend` and starts `app.main:app`.

The following are explicitly transitional and must not receive new architectural dependencies:

- `backend/app/routers/ai.py`
- `backend/app/services/llm_service.py`

`backend-v1.8/` and `backend-v2.1/` are historical generations and have been removed from `main`; their history is preserved in the archival branch created for the migration.

## Safe migration sequence

1. Freeze new cross-boundary dependencies in `backend/`.
2. Define integration contracts and authentication.
3. Move deterministic ERP code into `ERP-BACKEND/` in tested slices.
4. Extract AI/LLM code into `AI-BACKEND/`.
5. Update Compose, CI/CD, tests, and deployment references.
6. Run API, database migration, integration, and smoke tests.
7. Remove the legacy `backend/` tree only after runtime parity is verified.

## Data ownership

- ERP database: transactional ERP truth.
- AI memory/vector/index stores: derived AI context only.
- Integration events: immutable communication records; not a replacement for ERP transactions.
- Audit records: retain actor, action, target, timestamp, and correlation/request identifiers.

Never solve an architectural boundary violation by duplicating the ERP database inside the AI service.