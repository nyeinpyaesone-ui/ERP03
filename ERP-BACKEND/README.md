# ERP Backend — System of Record

`ERP-BACKEND/` is the target ERP system-of-record boundary defined by the architecture blueprint.

## Owns

- HTTP/API boundary
- authentication and authorization
- deterministic business rules
- domain entities and application services
- repositories and persistence
- database migrations
- transactions and validation
- audit/change tracking
- reporting/query services

## Hard boundary

ERP code must not depend on AI models, prompts, agent orchestration, memory stores, or LLM SDKs.

AI access to ERP capabilities is mediated by `INTEGRATION/` contracts and authenticated API/event interfaces.

## Migration status

The currently deployed FastAPI implementation is still physically located in `backend/`. It remains there temporarily because the root Compose runtime still builds `./backend`.

Do **not** delete or blindly copy the legacy backend. Migrate production code into this boundary in tested slices, then remove the legacy tree only after runtime, database migrations, API compatibility, and CI checks pass.

See `docs/architecture/BOUNDARIES.md` for the migration rules.