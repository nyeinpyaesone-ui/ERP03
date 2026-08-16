# ERP03 — ERP System of Record + External AI Platform

ERP03 is a modular ERP platform whose transactional ERP backend is kept independent from the AI/agent system.

## Architecture

```text
PROJECT/
├── ERP-BACKEND/          # ERP system of record
│   ├── app/              # FastAPI application
│   ├── alembic/          # Database migrations
│   └── frontend-react/   # ERP web client currently coupled to this service build
│
├── AI-BACKEND/           # AI / agent ownership boundary
├── INTEGRATION/          # API/event/schema/authentication bridge
├── INFRASTRUCTURE/       # Ollama, Redis, Postgres, deployment
├── docs/                 # Architecture and operations
└── scripts/              # Repository automation
```

### Boundary rules

- ERP owns transactional truth, authorization, workflows, and persistence.
- AI does not import ERP ORM models or connect directly to the ERP database.
- ERP ↔ AI communication goes through `INTEGRATION/` contracts.
- AI memory and model state are derived data, never a second ERP system of record.
- Legacy source generations are preserved in Git history instead of remaining in the active runtime tree.

## Current migration stage

The legacy `backend/` runtime has been migrated to `ERP-BACKEND/` on `main`.

The former in-process AI/LLM modules were removed from the ERP runtime:

- `backend/app/routers/ai.py`
- `backend/app/routers/llm.py`
- `backend/app/services/llm_service.py`
- `backend/app/knowledge/`

Their historical source remains recoverable through Git history/archive branches. The AI replacement service must be implemented behind `AI-BACKEND` and `INTEGRATION` before those user-facing AI capabilities are re-enabled.

## Development

```bash
cp .env.example .env
docker compose up -d
```

ERP API: `http://localhost:8000`  
ERP frontend: `http://localhost:3000`  
Ollama: `http://localhost:11434`

## Validation

```bash
./scripts/health-check.sh
docker compose config
docker build ./ERP-BACKEND -f ./ERP-BACKEND/Dockerfile -t erp03-backend:ci
docker build ./ERP-BACKEND/frontend-react -f ./ERP-BACKEND/frontend-react/Dockerfile -t erp03-frontend:ci
```

## Production data management

- Never commit real credentials, API keys, passwords, or production `.env` files.
- Use GitHub Actions secrets / deployment secret stores for credentials.
- Keep one authoritative write path for ERP transactional data during service extraction.
- Preserve migration and audit history; do not copy production databases into AI services.

## Repository history

Historical backend generations and the pre-boundary runtime remain available through Git history/archive branches. The active `main` tree contains maintained code and explicit architecture boundaries only.
