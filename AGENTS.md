# ERP03 — Agent Instructions

Production FastAPI backend (`ERP-BACKEND/`), React/Vite frontend (`frontend/`), Terraform infra (`infra/`). Single deployable unit.

## The two-command contract (everything)

Run these, in order, in every environment:

```bash
bash scripts/agent/bootstrap.sh   # idempotent; safe to re-run (creates .venv)
bash scripts/agent/verify.sh      # the only completion gate (writes .agent/evidence/*.json)
```

A task is **not** complete without `RESULT PASS`. Quote `.agent/evidence/<stamp>.json` and the `RESULT` line.

`make agent-verify` = `scripts/agent/verify.sh` = `scripts/qualify.sh` (ruff → compile → migrate → tests → frontend build). Do not run two different verification gates.

## Exact commands

Run from repo root unless noted.

| Purpose | Command |
|---------|---------|
| Bootstrap | `bash scripts/agent/bootstrap.sh` |
| Full setup (dev env) | `./scripts/setup.sh` |
| Full gate (completion) | `bash scripts/agent/verify.sh` |
| Lint + format | `cd ERP-BACKEND && ruff check app tests alembic && ruff format --check app tests alembic` |
| Tests | `cd ERP-BACKEND && pytest -q` (57 passed, 1 skipped — PG-only concurrency test skips on SQLite) |
| Single test | `cd ERP-BACKEND && .venv/bin/pytest tests/test_api.py -k <name> -q` |
| Alembic head | `cd ERP-BACKEND && .venv/bin/alembic heads` (single head expected — currently `0009_invoice_numbering_index`) |
| Migrate | `cd ERP-BACKEND && DATABASE_URL=<url> .venv/bin/alembic upgrade head` (before backend start) |
| Frontend build | `./scripts/build-frontend.sh` (Vite 5.4.11) |
| Start backend | `cd ERP-BACKEND && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000` |

CI uses Python 3.12 / Node 22; local Python may be 3.14 (asyncpg 0.32.0 works on 3.14). Frontend is Vite 5.4.11 (not Vite 7).

## Critical invariants (verify before changes)

| Invariant | How to check |
|-----------|--------------|
| GitHub Actions pinned to full commit SHAs | `python scripts/pin-github-actions.py --check` must PASS (`sha_pinning_required=true`; 23 refs) |
| Single Alembic head | `alembic heads` returns one revision (`0009_invoice_numbering_index`) |
| `Settings.extra == "forbid"` | Any undeclared env var → startup crash (`app/core/config.py`) |
| Production rejects SQLite | `ENVIRONMENT=production` + SQLite URL → `ValueError` (`app/core/config.py`) |
| Ruff config in `pyproject.toml` | target-version py312, line-length 100, excludes `alembic/versions` from src but `ruff check` still scans `alembic/` dir |

## Environment & secrets

Two local files — never mix:

- `ERP-BACKEND/.env` — backend runtime settings (`SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, `REDIS_URL`)
- `.env.compose` — root Compose interpolation (`POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `ERP03_BACKEND_IMAGE`, `ERP03_FRONTEND_IMAGE`, `IMAGE_TAG`, `DATABASE_URL`, `CORS_ORIGINS`)

The Compose file is not read by the backend directly; Compose injects only declared Settings fields into the container. Generated production configuration requires `ERP03_CORS_ORIGINS` to contain HTTPS origins.

GHCR images (multi-arch amd64/arm64): `ghcr.io/nyeinpyaesone-ui/erp03-backend` and `ghcr.io/nyeinpyaesone-ui/erp03-frontend`. Prefer immutable digests for deployments.

GitHub Actions uses its built-in `GITHUB_TOKEN` for GHCR. Do not create Docker Hub PATs for the current pipeline. Deployment SSH private keys and pinned known-hosts data are Environment secrets; non-sensitive host/user/path/port values are Environment variables. Never commit credentials, `.env` files, or anything under `secrets/` or `.agent/`.

## Database & migrations

- Single head only (`0009_invoice_numbering_index`); review generated migrations in `alembic/versions/`.
- `alembic upgrade head` before starting the backend.
- Integration tests require PostgreSQL; `qualify.sh` falls back to hermetic SQLite when PG is unreachable (expected in proot/Termux).
- Markers: `integration`, `requires_database`. There is no `postgres` marker.

## Idempotency & concurrency (core domain logic — easy to get wrong)

POS sale (`app/services/sales.py`):
- Fingerprint = SHA-256(canonical JSON of the sale command); key = `{business_id}:{client_idempotency_key}`
- Conflict codes: `IDEMPOTENCY_PAYLOAD_MISMATCH` | `IDEMPOTENCY_KEY_REUSED`
- Locks: `SELECT ... FOR UPDATE` on Branch (serializes `invoice_no`), then Warehouse/Customer/Product; savepoint per InvoiceItem + Payment; duplicate `invoice_no` → replay existing.

Cross-module (`app/services/orchestration.py`):
- 6-state machine: `PENDING → PROCESSING → COMMITTED | FAILED → RECONCILIATION_REQUIRED | CANCELLED`
- Claim = conditional UPDATE; `SKIP LOCKED` on PostgreSQL, plain `FOR UPDATE` on SQLite
- Exponential backoff `2^retry_count` s (capped 1 hr); reconciliation reclaims stale `PROCESSING` (>5 min)

SQLite journal (`app/core/transaction_store.py`): WAL mode + `BEGIN IMMEDIATE`; legacy rows without fingerprint → `IDEMPOTENCY_KEY_REUSED`.

## Rate limiting (Redis-backed)

`RedisRateLimitMiddleware` (`app/main.py`): Redis ZSET sliding window; returns 429 + `Retry-After`. Settings: `rate_limit_enabled`, `rate_limit_requests`, `rate_limit_window`, `redis_url`, `trusted_proxies`.

## TypeSafe (optional)

Enable: `TYPESAFE_ENABLED=true`, `TYPESAFE_API_KEY=<key>`. Non-blocking (error returned even if TypeSafe fails). Confidence: act ≥ 0.70, escalate ≥ 0.40; risk score ≥ 75 is a high-risk gate; same command → replay.

## Common tasks

Add a new API endpoint: schema in `app/schemas/<domain>.py` → service in `app/services/<domain>.py` → route in `app/api/<domain>.py` → `app.include_router(...)` in `app/main.py` → test in `tests/test_<domain>.py`. Not live until registered in `main.py`.

Add a DB column: modify `app/models/*.py` → `alembic revision --autogenerate -m "<name>"` → review `alembic/versions/` → `alembic upgrade head`.

## CI workflows

| Workflow | Trigger | Responsibility |
|----------|---------|----------------|
| `ci.yml` | push/PR `main`, manual dispatch, reusable call | PostgreSQL + Redis → compile → migrate → pytest → frontend build |
| `quality.yml` | push/PR `main`, reusable call | Ruff check/format + compile |
| `policy.yml` | push/PR `main`, manual dispatch | Kustomize render + Conftest policy checks; run #486 on PR #318 ended `startup_failure` with zero jobs and remains under investigation |
| `docker-publish.yml` | push `main`, schedule, PR, reusable Release call | Signed backend GHCR multi-arch image + SBOM/provenance + manifest and signature verification |
| `container.yml` | push `main` / `release/**`, PR, reusable Release call | Frontend GHCR multi-arch image + SBOM/provenance + manifest verification |
| `release.yml` | push tags `v*` | CI + Quality → signed backend + frontend images → GitHub Release |
| `deploy-staging.yml` | manual dispatch | Staging environment; immutable digests; SSH health checks and rollback |
| `production-deploy.yml` | manual dispatch from `main` + explicit confirmation | Production environment; immutable tag; server-managed env file; health verification |
| `deploy-canary.yml` | manual dispatch | Disabled legacy placeholder; fails closed |
| `rotate-secrets.yml` | manual dispatch | Audit acknowledgement only; no credential rotation |

Internal hand-offs use `workflow_call` and `needs`; avoid `workflow_run` chains for deterministic release dependencies. External producers may use `repository_dispatch` only after a typed event contract is defined. All referenced Actions remain pinned to full commit SHAs.

## Local development quirks (verified)

| Issue | Workaround |
|---------|------------|
| `gh auth` (no browser) | `echo "<pat>\|gh auth login --with-token` |
| Docker unavailable (proot/Termux) | `[SKIP] docker reason=no-daemon` expected; never fake a pass |
| `[SKIP] postgres reason=sqlite-fallback` | Expected when PG unreachable; suite fully green on SQLite |

Environment differences (proot arm64, Codespaces, CI) live inside `scripts/agent/`. **Never hardcode `apt`, `sudo`, `docker` or `systemd`.** See `docs/agent/ENVIRONMENTS.md` and `docs/agent/WORKFLOW.md`.

## Boundaries (do not)

- Do not add dependencies to make a gate pass.
- Do not disable a gate (`|| true`, `continue-on-error`, `# noqa`) to go green.
- Do not commit `.env`, `secrets/`, or `.agent/`.
- Do not force-push or rewrite history; no credential rotation without approval.

## References

- `docs/agent/WORKFLOW.md` — agent loop (detect → bootstrap → work → verify → evidence → commit)
- `docs/agent/ENVIRONMENTS.md` — per-environment capability matrix
- `scripts/pin-github-actions.py` — SHA-pin audit (`--check` must PASS)
- `docs/PR_MERGE_ORDER.md` — merge sequence for open PRs
- `infra/` — Terraform modules for cloud deployment
