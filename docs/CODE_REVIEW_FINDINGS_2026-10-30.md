# ERP03 Code Review — Findings (2026-10-30)

Scope: `ERP-BACKEND/`, `frontend/`, compose/Docker. Verification baseline:
`ruff check` 0 findings, `ruff format --check` clean, `compileall` OK,
`alembic heads` single (0007), `pytest` 52 passed / 1 skipped.

Severity: **P0** blocks startup/CI/contract · **P1** correctness/security with workaround · **P2** hygiene/docs.

## P0

### P0-1 — Idempotency key overflow on `Invoice` path
- **Where**: `ERP-BACKEND/app/api/sales.py` (`idempotency_key=f"{business_id}:{idempotency_key}"`) → `app/services/sales.py` stores it in `Invoice.idempotency_key` (`String(255)`).
- **Issue**: `validate_idempotency_key` allows up to 255 chars; the prefixed value is `36 (uuid) + 1 + up to 255 = 292` chars, exceeding the column → DB `DataError`/`IntegrityError` on any near-max key. `TransactionStore` (TEXT) is unaffected.
- **Fix**: validate combined length ≤ 255 in `validate_idempotency_key` (or reduce the allowed raw length to 218), and add a regression test with a 220-char key.

### P0-2 — Frontend container cannot bind port 80
- **Where**: `frontend/Dockerfile` (`USER app` with nginx listening on 80).
- **Issue**: nginx master runs as `app` (uid 1000) and cannot bind a privileged port → container fails to start.
- **Fix**: either drop `USER app` (run master as root, workers as nginx) or switch nginx to listen on 8080 and map `80:8080` in compose; keep the healthcheck aligned.

## P1

### P1-1 — Rate limiter is not proxy-aware (shared bucket behind a load balancer)
- **Where**: `ERP-BACKEND/app/main.py` `RateLimitMiddleware.__call__` uses `scope["client"][0]` only.
- **Issue**: behind nginx/ALB all traffic appears as one IP → one global bucket → trivial self-DoS / bypass.
- **Fix**: trust `X-Forwarded-For` only from a configured trusted-proxy list, or move limiting to the gateway/Redis.

### P1-2 — In-memory rate limiter is per-process
- **Where**: same; `self.requests` dict.
- **Issue**: with multiple workers/replicas limits are not enforced globally; also unbounded growth of the dict (no eviction of idle IPs).
- **Fix**: add periodic cleanup of stale IP entries (or use a bounded LRU); document single-process scope, or replace with Redis-backed limiter.

### P1-3 — `TransactionStore` is a process-local singleton
- **Where**: `ERP-BACKEND/app/api/transactions.py` (`store = TransactionStore(settings.database_path)` at import).
- **Issue**: each worker/replica has its own SQLite journal → no cross-process idempotency; sync blocking store inside async app. Acceptable for single-process but undocumented.
- **Fix**: document the single-process constraint, or make the store async/process-shared; ensure tests use a fresh store per test (fixture).

### P1-4 — Vite dev proxy strips `/api` incorrectly
- **Where**: `frontend/vite.config.js` `rewrite: (path) => path.replace(/^\/api/, '')`.
- **Issue**: `/api/healthz` → `/healthz`, but backend serves `/api/v1/healthz` → 404 in dev. Prod (nginx) is correct.
- **Fix**: rewrite to `/api/v1` (or stop stripping and proxy to `/api/v1`).

### P1-5 — `next_invoice_no` relies on string `max` + branch lock
- **Where**: `ERP-BACKEND/app/services/sales.py` `next_invoice_no`.
- **Issue**: gap-free numbering depends on the branch-row lock; if a client supplies `invoice_no`, the unique constraint catches collisions. Minor risk: `int(last[len(prefix):])` assumes 6-digit zero-padded suffix; malformed historical rows could raise `ValueError`.
- **Fix**: guard parsing with `try/except` and fall back to 1; add a test for a malformed prior invoice_no.

### P1-6 — `Permission`/`Role` tables lack `active`/audit columns (minor)
- **Where**: `app/models/identity.py`.
- **Issue**: roles/permissions cannot be deactivated; not a current bug but limits RBAC lifecycle. Noted for future.

### P1-7 — `adjust_stock` creates balance lazily only on positive delta
- **Where**: `ERP-BACKEND/app/services/inventory.py`.
- **Issue**: receiving into a warehouse with no prior balance creates a zero balance then adds — OK. But if a product is received before any sale, fine. Negative delta with no balance raises `InsufficientStockError` — correct. No bug, but the `flush()` inside is fine.

## P2

### P2-1 — Frontend Dockerfile omits `vite.config.js`
- **Where**: `frontend/Dockerfile` COPY list.
- **Issue**: build relies on env + default Vite behavior; `vite.config.js` (proxy/define) not used in container build. Build still succeeds, but config drift.
- **Fix**: `COPY vite.config.js ./` before build.

### P2-2 — `vite` listed under `dependencies` instead of `devDependencies`
- **Where**: `frontend/package.json`.
- **Fix**: move `vite` to devDependencies.

### P2-3 — Dev compose runs `pip install` on every backend start
- **Where**: `docker-compose.dev.yml` backend command.
- **Issue**: slow restarts; should rely on image deps. Minor.

### P2-4 — Docs drift: `scripts/build-frontend.sh` referenced but absent
- **Where**: `AGENTS.md` references `./scripts/build-frontend.sh`; file does not exist.
- **Fix**: update docs or add the script.

### P2-5 — `validate_password_policy` (12..256) vs `Settings.password_min_length` (default 8)
- **Where**: `app/services/bootstrap.py` vs `app/core/config.py`.
- **Issue**: bootstrap enforces 12 min while config says 8; login/other paths use config? Auth router doesn't enforce password policy at all (only bootstrap does). Inconsistent.
- **Fix**: unify on `Settings.password_min_length` everywhere a password is set.

### P2-6 — No `max` on `credit_limit`/`payable_balance` etc.
- Minor; not blocking.

## Verification commands (re-run after fixes)
```bash
cd ERP-BACKEND
ruff check app tests alembic
ruff format --check app tests alembic
python -m compileall -q app alembic
alembic heads
alembic upgrade head
pytest -q
```

## Notes
- Quality gate currently green (52 passed, 1 skipped). Findings above are design/robustness, not test failures.
- Jev skills now installed (simulation mode) under `~/.config/opencode/skills`; `jev-code-review` can be used for hunk-level review leads.
