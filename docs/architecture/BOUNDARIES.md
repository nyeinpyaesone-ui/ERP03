# ERP / AI Architecture Boundaries

## Target structure

```text
PROJECT/
├── ERP-BACKEND/       # ERP System of Record
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

ERP remains authoritative for transactional truth. AI is a consumer/orchestrator and must not become a second system of record.

## Completed migration stage — 2026-08-16

- `backend/` has been removed from `main`.
- The maintained FastAPI ERP runtime now lives at `ERP-BACKEND/`.
- ERP startup no longer imports or mounts the former in-process AI router.
- `backend/app/routers/ai.py`, `backend/app/routers/llm.py`, and `backend/app/services/llm_service.py` are no longer part of the ERP runtime.
- The former `backend/app/knowledge/` tree is no longer part of the ERP runtime.
- The old backend compose file was removed; the repository-root Compose file is canonical.
- CI, release builds, Docker build scripts, production Compose, and Nginx references now use `ERP-BACKEND`.
- `backend-v1.8/` and `backend-v2.1/` remain historical generations outside `main` through the archival Git history.

## AI runtime boundary

`AI-BACKEND/` is now the designated ownership boundary. The previous in-process AI implementation is preserved by Git history rather than duplicated into the active source tree. The replacement AI runtime must use `INTEGRATION/` contracts for ERP data and commands and must not directly import ERP ORM models or connect to the ERP database.

This deliberately makes the ERP boundary clean before reintroducing AI behavior. It avoids the common migration failure mode of creating a new service while retaining the old code path in the monolith.

## Next atomic stage

1. Implement the AI runtime inside `AI-BACKEND/`.
2. Define authenticated ERP read/query contracts in `INTEGRATION/`.
3. Route AI UI/API consumers to `AI-BACKEND/`.
4. Add AI-specific persistence for conversations, memory, usage, and policies where required.
5. Add end-to-end ERP ↔ integration ↔ AI tests.
6. Re-enable AI routes only after the replacement service has parity for the required user-facing capabilities.

## Data ownership

- ERP database: transactional ERP truth.
- AI persistence: derived AI state, conversations, memory, and usage only.
- Integration events/contracts: communication boundary, not a replacement for ERP transactions.
- Audit records: actor, action, target, timestamp, and correlation/request identifiers.

Never solve a boundary violation by duplicating the ERP database inside the AI service.
