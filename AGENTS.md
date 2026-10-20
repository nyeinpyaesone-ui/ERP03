# ERP03 — Agent instructions

Production-focused AI ERP modular-monolith. FastAPI backend (`ERP-BACKEND/`), React/Vite frontend (`frontend/`), Terraform infra (`infra/`). Single deployable unit; capabilities are added behind app/domain boundaries, not premature service splits.

## Layout & entry points

| Path | Role |
|---|---|
| `ERP-BACKEND/app/main.py` | FastAPI app, `lifespan` binds TypeSafe client close |
| `ERP-BACKEND/app/core/config.py` | `Settings` with `extra="forbid"` |
| `ERP-BACKEND/app/core/errors.py` | Typed `AppError` codes (INTERNAL_ERROR, VALIDATION_ERROR, CONFLICT, NOT_FOUND, FORBIDDEN, …) |
| `ERP-BACKEND/app/core/typesafe.py` | Optional System One judgments (error classification, transaction risk, idempotency conflict) |
| `ERP-BACKEND/app/api/transactions.py` | Journal endpoints; typed idempotency codes `IDEMPOTENCY_PAYLOAD_MISMATCH` / `IDEMPOTENCY_KEY_REUSED` |
| `ERP-BACKEND/app/services/sales.py` | Atomic POS sale: invoice + stock + payments in one DB transaction |
| `ERP-BACKEND/app/services/orchestration.py` | 6-state cross-module operation state machine |
| `ERP-BACKEND/alembic/versions/` | Single head `0007_operation_orchestration` |
| `frontend/` | Vite dev server on 5173; prod nginx build on port 80 |

## Verification endpoints

- `GET /api/v1` — API identity
- `GET /api/v1/healthz` — liveness
- `GET /api/v1/readyz` — database + migration readiness
- `GET /api/v1/docs` — API docs
- `GET /api/v1/metrics` — Prometheus

## Exact developer commands

Run from repo root unless noted.

```bash
# Bootstrap (creates .venv at root, ERP-BACKEND/.env, runs smoke tests)
./scripts/setup.sh
./scripts/setup.sh --qualify          # full CI-equivalent gate
./scripts/setup.sh --with-infra       # also start Docker Compose

# Activate backend env
source .venv/bin/activate             # venv lives at repo root

# Lint (must pass before commit)
cd ERP-BACKEND && ruff check app tests alembic
cd ERP-BACKEND && ruff format --check app tests alembic

# Compile + migrations + tests
cd ERP-BACKEND
python -m compileall -q app alembic
alembic upgrade head                  # single head; fresh-DB apply verified
pytest -q                             # 48 passed, 1 PG-only skip

# Frontend
cd frontend && npm ci && npm run build

# Dev compose (Vite HMR on 5173, backend on 8000, postgres 5432)
docker compose -f docker-compose.dev.yml up --build   # or: make dev

# Prod compose
docker compose up --build                    # minimal: backend + frontend (+ SQLite journal)
docker compose --profile full up             # + managed Postgres + migration job

# Make targets
make dev | test | lint | build | up | down | build-backend | build-frontend | build-all
```

## Environment gotchas (verifiable, not speculative)

- **`Settings(extra="forbid")`** — any env var not declared in `app/core/config.py` crashes startup. Keep backend keys in `ERP-BACKEND/.env.example`, compose-only keys in root `.env.compose.example`. Never mix them.
- **Production validation**: `ENVIRONMENT=production` rejects SQLite `DATABASE_URL`, requires `SECRET_KEY` ≥32 chars, HTTPS-only non-local CORS origins, and PostgreSQL `DATABASE_URL`.
- **Paths differ by context**: compose uses `/app/.local/erp03.sqlite3`; local venv uses a CWD-relative or temp path. `setup.sh` generates `ERP-BACKEND/.env` with the container path for Docker use.
- **`requirements.txt` ships test deps** (pytest, pytest-asyncio, httpx) in the prod image — known, do not remove without updating CI install steps.
- **`VITE_API_BASE_URL` is build-time evaluated** in the frontend; it is not read at runtime by nginx. Default relative base + nginx `/api/` proxy is the deploy-safe pattern.
- **Frontend dev port is 5173**; prod frontend serves on port 80 (mapped to 3000 in compose).

## CI / quality

Workflows (all `ubuntu-latest`):
- `ci.yml` — backend (Postgres service → compile → `alembic upgrade head` → pytest) + frontend (npm install + build)
- `quality.yml` — ruff check/format + compileall + frontend build
- `security.yml` — pip-audit + CodeQL
- `container.yml` — image build + Trivy
- `iac.yml` — terraform fmt/validate/plan + artifact upload
- `release.yml` — workflow_dispatch SemVer release

Concurrency groups cancel in-progress runs on the same ref (`ci-${{ github.ref }}`, `quality-${{ github.ref }}`).

Merge order (see `docs/PR_MERGE_ORDER.md`): #170 (security/env rotation) → Dependabot #191–196 → #229/#228. Do not merge any PR unless its head commit CI is green.

## Alembic

Single head `0007_operation_orchestration`. Always run `alembic upgrade head` against a fresh DB before starting the backend; the compose `migrate` service does this and `backend` depends on `service_completed_successfully`.

## TypeSafe integration (optional, disabled by default)

`app/core/typesafe.py` — gated by `TYPESAFE_ENABLED` + `TYPESAFE_API_KEY`. Code owns decisions; TypeSafe only annotates:
- Confidence thresholds: act ≥0.70, escalate <0.40
- `classify_error` → drives `Retry-After` header on error responses
- `judge_request` asks independent judgments in parallel via `asyncio.gather`
- Client closed in FastAPI `lifespan` shutdown
- Never sniff error-message text for codes; use typed `IdempotencyConflict.code`

## Do not commit

`.venv/`, `.env`, `frontend/node_modules/`, `frontend/dist/`, `__pycache__/`, `.ruff_cache/`, `*.pyc`. Secrets go in environment variables only; `setup.sh` generates a random `SECRET_KEY` into `ERP-BACKEND/.env` (chmod 600).
