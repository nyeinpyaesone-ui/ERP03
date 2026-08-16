# AI Backend — AI / Agent System

`AI-BACKEND/` is a separate AI/agent runtime outside the ERP system of record.

## Owns

- AI API routes
- orchestrator and task planning
- specialist agents
- model/LLM routing
- tool execution
- memory and retrieval
- AI policies and safety controls
- AI-specific events and audit records

## Hard boundary

AI must not import ERP ORM models, repositories, database sessions, migrations, or internal business services.

ERP interaction must use `INTEGRATION/` contracts through authenticated API calls or approved events.

## Migration status

The existing AI implementation inside `backend/app/routers/ai.py` and `backend/app/services/llm_service.py` is transitional legacy code. It must be extracted into this boundary before those files are removed.

Migration order:

1. define integration contracts;
2. implement AI service behind the contracts;
3. migrate callers and tests;
4. remove ERP-side AI wiring;
5. delete the legacy AI files.

See `docs/architecture/BOUNDARIES.md`.