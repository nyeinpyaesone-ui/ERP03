# ERP03

Production-focused AI ERP modular-monolith foundation.

## Current runtime
- FastAPI API on port 8000
- React/Vite client on port 3000
- Docker Compose for local system integration
- Deterministic Python dependency versions
- CI qualification for backend compile/tests and frontend build

## Verification endpoints
- `GET /api/v1` — API identity
- `GET /api/v1/healthz` — liveness
- `GET /api/v1/readyz` — transactional database + schema-migration readiness

## Architecture direction
ERP remains the transactional authority. Business capabilities are added behind explicit application/domain boundaries rather than splitting the system prematurely into services.

Target capability sequence: authentication → business profile → capability registry/compiler → policy/context → runtime/workflow → approvals/audit → control tower → AI agent integration → end-to-end qualification.

## Automated setup (Linux · macOS · WSL)
```bash
./scripts/setup.sh                # toolchain detection, venv, deps, secure .env, smoke tests
./scripts/setup.sh --with-infra   # additionally start the Docker Compose stack
./scripts/setup.sh --qualify      # run the full CI-equivalent qualification gate
```

The script detects the host platform and package manager, verifies Python ≥ 3.12
and Node ≥ 18, provisions an isolated virtualenv with pinned dependencies, and
generates a random `SECRET_KEY` into `.env` when one is missing.

## Local run (Docker)
```bash
cp ERP-BACKEND/.env.example .env   # then set SECRET_KEY / POSTGRES_PASSWORD / CORS_ORIGINS
docker compose up --build          # minimal profile: backend + frontend (+ SQLite journal)
docker compose --profile full up   # managed PostgreSQL instance with migration job
```

Frontend: `http://localhost:3000`
API docs: `http://localhost:8000/docs`
Metrics: `http://localhost:8000/metrics` (Prometheus)

Do not commit secrets. Configure runtime values through environment variables.
