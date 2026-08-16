# Legacy Backend — Migration Boundary

This directory is the current runtime implementation, not the final architectural location.

## Status

- Runtime-critical: **yes**
- New architectural development: **no**
- Target: `ERP-BACKEND/`
- AI extraction target: `AI-BACKEND/`

Do not add new direct ERP↔AI coupling here. Keep changes limited to bug fixes, compatibility work, and migration steps until the runtime is moved and validated.

### AI files awaiting extraction

- `app/routers/ai.py`
- `app/services/llm_service.py`

These files must be migrated before deletion because `app/main.py` currently imports and registers the AI router.