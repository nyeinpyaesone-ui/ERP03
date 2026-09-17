# ERP03

Production-focused AI ERP modular-monolith foundation.

## Current runtime
- FastAPI API on port 8000
- React/Vite client on port 3000
- Ollama integration endpoint for local AI readiness
- Docker Compose for local system integration
- Deterministic Python dependency versions
- CI qualification for backend compile/tests and frontend build

## Verification endpoints
- `GET /api/v1` — API identity
- `GET /api/v1/healthz` — liveness
- `GET /api/v1/readyz` — Ollama dependency readiness

## Architecture direction
ERP remains the transactional authority. Business capabilities are added behind explicit application/domain boundaries rather than splitting the system prematurely into services.

Target capability sequence: authentication → business profile → capability registry/compiler → policy/context → runtime/workflow → approvals/audit → control tower → AI agent integration → end-to-end qualification.

## Local run
```bash
docker compose up --build
```

Frontend: `http://localhost:3000`
API docs: `http://localhost:8000/docs`

Do not commit secrets. Configure runtime values through environment variables.
