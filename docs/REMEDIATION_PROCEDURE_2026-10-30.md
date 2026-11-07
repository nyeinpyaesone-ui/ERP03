# ERP03 Remediation Procedure — Final Stage

**Source findings:** `docs/CODE_REVIEW_FINDINGS_2026-10-30.md`
**Methodology:** follows `docs/TODO.md` (branch → reproduce → minimal fix → mandatory gate → record SHA).
**Branch base:** latest `origin/main`.

## Mandatory verification gate (run after every item)

```bash
cd ERP-BACKEND
.venv/bin/ruff check app tests alembic
.venv/bin/ruff format --check app tests alembic
.venv/bin/python -m compileall -q app alembic
.venv/bin/alembic heads          # exactly one head
.venv/bin/alembic upgrade head   # fresh-DB apply
.venv/bin/python -m pytest -q    # 0 failed; PG-only skips allowed
```

Frontend (when touched):
```bash
cd frontend && npm ci --no-audit --no-fund && npm run build
```

Record each completed item in `docs/TODO.md` "Done & verified" with commit SHA + evidence.

---

## Phase 0 — Preflight (once, before any fix)

1. `git fetch origin && git checkout main && git pull --ff-only`
2. `git checkout -b fix/review-findings-2026-10-30`
3. Confirm gate passes on clean tree (baseline).
4. Confirm no uncommitted changes: `git status --porcelain` empty.

---

## Phase 1 — P0 (block startup/contract) — do first, one commit each

### Step 1.1 — P0-1: idempotency key overflow
- **Reproduce**: write a quick test posting a sale with `X-Idempotency-Key` of 220 chars; expect 500/DB error.
- **Fix**: in `ERP-BACKEND/app/api/validation.py`, reduce `MAX_IDEMPOTENCY_KEY_LENGTH` so that `len(business_id) + 1 + len(key) <= 255` (i.e. 218). Alternatively widen `Invoice.idempotency_key` to `String(512)` via a new Alembic migration. Prefer the validation fix (smaller blast radius) and document the limit.
- **Files**: `app/api/validation.py`, `tests/test_sales*.py` (add regression).
- **Verify**: gate + new test passes with 220-char key returning 201 (or 400 if rejected).

### Step 1.2 — P0-2: frontend container privileged port
- **Reproduce**: `docker build frontend` then run; nginx fails to bind 80 as `app`.
- **Fix** (choose one, commit the choice):
  - Option A: remove `USER app` from `frontend/Dockerfile` (master as root, workers as nginx user) — simplest, matches official nginx image.
  - Option B: listen on 8080 + map `80:8080` in compose; update healthcheck.
- **Files**: `frontend/Dockerfile`, `docker-compose.yml`, `docker-compose.dev.yml`.
- **Verify**: `docker compose config` valid; frontend image `HEALTHCHECK` passes.

---

## Phase 2 — P1 (correctness/security) — one commit per item

### Step 2.1 — P1-5: `next_invoice_no` parsing guard (lowest risk, do first)
- **Fix**: wrap `int(last[len(prefix):])` in try/except, fall back to 1; add test with malformed prior `invoice_no`.
- **Files**: `app/services/sales.py`, `tests/test_invoice_numbering.py`.

### Step 2.2 — P1-4: Vite dev proxy
- **Fix**: change rewrite to keep `/api/v1` (or proxy target to `/api/v1` without stripping).
- **Files**: `frontend/vite.config.js`.
- **Verify**: `npm run dev` + curl `/api/healthz` returns 200.

### Step 2.3 — P1-2 / P1-1: rate limiter hardening
- **Fix**: (a) add trusted-proxy handling for `X-Forwarded-For`; (b) evict stale IP entries periodically; (c) document single-process scope or move to Redis.
- **Files**: `app/main.py`, `app/core/config.py` (trusted proxies setting), tests.
- **Note**: if moving to Redis, that's a larger change — scope to (a)+(b) now, Redis later.

### Step 2.4 — P1-3: `TransactionStore` test isolation
- **Fix**: add a pytest fixture providing a fresh store (tmp `database_path`) and override the module-level singleton in tests; document single-process limitation in AGENTS.md.
- **Files**: `tests/conftest.py`, `app/api/transactions.py` (optional factory), `AGENTS.md`.

### Step 2.5 — P1-6 / P1-7: RBAC lifecycle + stock (optional, low priority)
- Only if time permits; otherwise defer to next cycle.

---

## Phase 3 — P2 (hygiene/docs)

### Step 3.1 — P2-1 + P2-2: frontend Dockerfile + package.json
- Add `COPY vite.config.js ./`; move `vite` to devDependencies.
- **Verify**: `npm ci && npm run build`.

### Step 3.2 — P2-3: dev compose
- Remove `pip install` from backend command; rely on image.

### Step 3.3 — P2-4: docs drift
- Either add `scripts/build-frontend.sh` or update `AGENTS.md` to remove the reference.

### Step 3.4 — P2-5: password policy unification
- Use `Settings.password_min_length` in `validate_password_policy` and enforce in auth flows.

---

## Phase 4 — Final verification & close

1. Run full gate (above) on the branch.
2. Run frontend build.
3. Run compose config validation: `docker compose config`, `docker compose -f docker-compose.dev.yml config`.
4. Open PR; require CI green (CI-1/OPS-1).
5. After merge: update `docs/TODO.md` "Done & verified" table with SHAs; mark P0/P1 items complete.
6. Tag/release if applicable.

---

## Rollback

- Each item is one commit → `git revert <sha>` per item.
- If a phase fails the gate, revert the last commit and re-scope.

## Evidence to record (per item)

- Commit SHA
- Gate output summary (ruff 0, pytest N passed)
- For P0-1: test name + passing output with 220-char key.
- For P0-2: `docker compose config` output + successful container start log.
