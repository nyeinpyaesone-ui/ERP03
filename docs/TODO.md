# ERP03 Remediation Tracker

**Updated:** 2026-10-20 · **Source:** live verification session + full-repo re-audit
**Supersedes the task lists in** `REMAINING_TASKS.md` (kept for history).

## How to work this list (methodology)

Every item follows the same loop — no exceptions:

1. **Branch** from latest `origin/main` (`fix/<topic>` or `chore/<topic>`).
2. **Reproduce / evidence** the problem first (command + output recorded).
3. **Fix minimally** — one logical change per commit, conventional-commit message.
4. **Verify with the mandatory gate:**

   ```bash
   cd ERP-BACKEND
   .venv/bin/ruff check app tests alembic
   .venv/bin/ruff format --check app tests alembic
   .venv/bin/python -m compileall -q app alembic
   .venv/bin/alembic heads                     # exactly one head
   .venv/bin/alembic upgrade head              # fresh-DB apply
   .venv/bin/python -m pytest -q               # 0 failed; PG-only skips allowed
   ```

5. **Record evidence** (commit SHA + output summary) below.
6. **Move item to "Done & verified"** with its SHA.

Severity: **P0** = blocks startup/CI or breaks a client-visible contract · **P1** = correctness/security with workaround · **P2** = hygiene/docs/warnings.

---

## P0 — block startup/CI/contract

*(none open — both P0 items below were found and repaired in this round)*

## P1 — correctness / security

- [x] **FE-1: `VITE_API_BASE_URL` as runtime env is a no-op (agent finding 6).**
     _URL is evaluated at build time (`frontend/vite.config.js`, `App.jsx`);
      prebuilt GHCR images bake `http://localhost:8000/api/v1` in, breaking any
      real host deployment. Fix: default to relative base and rely on the
      existing nginx `/api/` proxy (`frontend/nginx.conf:9-10`), or accept the
      URL as a Docker build ARG. *Acceptance: built image serves API calls
      without runtime env.*
- [x] **TS-2: Legacy fingerprint-less replay semantics (agent finding 9).**
      Legacy rows without `request_fingerprint` replay silently on any payload;
      `IDEMPOTENCY_KEY_REUSED` is currently unreachable via data. Decide
      semantics (recommend: mismatch-on-fingerprint-less → `IDEMPOTENCY_KEY_REUSED`)
      and add a test that seeds a legacy row.
- [x] **METRICS-1: `/metrics` unauthenticated (agent finding 10).** Gate with
      auth claims or bind to an internal-only port/target. ✅ **VERIFIED** +
      **REGRESSION-TESTED**: `app/core/metrics.py` ASGI auth middleware (Bearer
      JWT via `decode_access_token`); no-auth → 401, invalid-token → 401,
      valid-token → 200. Added `test_metrics_requires_authentication`,
      `test_metrics_rejects_invalid_token`, `test_metrics_accepts_valid_token`
      in `tests/test_api.py`.
- [x] **AUTH-1: JWT TTL hardcoded 480 min, claims never re-validated against
      User/branch state (agent finding 11).** Add a Settings knob, re-check
      `User.active` on privileged endpoints or shorten TTL; consider login
      rate-limiting. ✅ **VERIFIED**: Settings knob exists
      (`jwt_expiry_minutes`, default 480, ge=1/le=44640); `create_access_token`
      consumes it; `require_permission` re-checks `User.active`/`Business.active`
      + permission joins. ✅ **RATE LIMITING IMPLEMENTED**: `RateLimitMiddleware`
      in `app/main.py` with config via `rate_limit_enabled`,
      `rate_limit_requests`, `rate_limit_window`; default 100 req/min per IP;
      returns 429 + `Retry-After` header.
- [x] **SETP-1: setup.sh emits container-absolute SQLite path for host use
      (agent finding 12).** Point `database_url`/`database_path` at the same
      venv-local absolute file. ✅ **FIXED**: `setup.sh` now uses `$ROOT_DIR/ERP-BACKEND/.local/erp03.sqlite3` consistently in both dev/prod configs; `DATABASE_PATH` empty in prod (PostgreSQL); verified Settings loads clean.
- [x] **QUAL-1: qualify.sh assumes a pre-provisioned PG with fixed creds and
      no precondition probe (agent finding 13).** Probe first, print
      actionable hint, hermetic fallback.
      ✅ **VERIFIED**: `scripts/qualify.sh` now contains `probe_postgres()` +
      `USE_PG` fallback to hermetic SQLite (`/tmp/erp03-qualify.sqlite3`).
- [x] **CI-1: Frontend installs ignore the lockfile (agent finding 8).**
      `frontend/Dockerfile`, `ci.yml:75-81`, `qualify.sh:47` — switch to
      `npm ci` and lock the Express and `cache-dependency-path` to
      `package-lock.json`.
      ✅ **VERIFIED+FIXED**: `frontend/Dockerfile` uses `npm ci`; `ci.yml:71` uses
      `npm ci` + `cache-dependency-path: frontend/package-lock.json`; `quality.yml`
      fixed this round (`npm install`→`npm ci`, `cache-dependency-path`→
      `frontend/package-lock.json`); `scripts/qualify.sh` fixed this round
      (`npm install`→`npm ci`). YAML validated.
- [ ] **OPS-1: CI green evidence on `ubuntu-latest` (agent finding 4
      residue).** Confirm the run for `f6f25b21` is green across
      CI/Quality/Security/Container/IaC before closing #224/#226.
- [ ] **PR-1: Merge queue.** After OPS-1: #170, Dependabot #191-196, then
      #229/#228/#220.

## P2 — hygiene / docs / staging evidence

- [ ] **DOC-1: matrix vs REMAINING_TASKS contradiction (agent finding 15).**
      matrix rows assert PASS/QUALIFIED that no run artifact backs; downgrade
      to real states with artifact links (or move the UNTIL evidence here).
- [ ] **MIG-1: matrix migration both DROP? no — only after: re-run check:
      confirm 0006/0007 types match models (agent finding 5 fixed for
      `operations`; audit other JSON columns for the same Text-mismatch
      class).**
- [ ] **OPS-2: Container build + Trivy evidence in Codespace (daemon needed).**
- [ ] **OPS-3: Backup drill: restore dump into scratch PG + alembic_version
      probe (agent finding 14); backup_verify.sh currently only checks gzip CRC.**
- [ ] **ALERT-1: `promtool check rules` + load once in staging Prometheus;**
- [x] **DEP-2: Move pytest/pytest-asyncio/httpx out of prod requirements**
      (agent finding 18) — CI depends on them only because they ship in prod;
      correct ci.yml deps then trim requirements (agent finding 18)
      and ci.yml: install dev-requirements for the test job. ✅ **VERIFIED**:
      Already separated — `requirements.txt` has only prod deps;
      `dev-requirements.txt` has pytest/pytest-asyncio/httpx/ruff/typesafe;
      `ci.yml` installs both for test job; `quality.yml` installs only prod + ruff.
- [x] **DEP-2b: delete stray root `package-lock.json`** (agent finding 17).
      ✅ **VERIFIED**: No stray root `package-lock.json` exists.
- [x] **DEVOPS-1: `migrate` advisory depends_on lets API boot with no tables
      (agent finding 16) — set `required: true`.** ✅ **FIXED**: `docker-compose.yml`
      backend `depends_on.migrate.required: true` added in commit `860dfcaf`.
- [x] **T-1: 36 pytest library-deprecation warnings — track, don't suppress.**
      ✅ **DONE**: Added `filterwarnings = default::DeprecationWarning` and
      `default::PendingDeprecationWarning` to `ERP-BACKEND/pytest.ini`
      to track all deprecation warnings without suppressing them.

---

## Done & verified

| Item | Evidence | Commit |
|---|---|---|
| P0 ENV-1: prod compose defaulted SQLite+production (validator-crash); no `.env.example` | compose interpolation OK; Settings prod+PG OK, prod+SQLite rejected | `73ecc902` |
| P0 Dockerfile: pip --user to root-only /root/.local, no --chown, stray `$PYTHONPATH` in PATH → runtime image broken | deps now to shared `/opt/appdeps`, `--chown` at copy, PATH corrected; runtime env compileall/pytest green | `f6f25b21` |
| P0 frontend build broken: `@vitejs/plugin-react` missing from pkg+lock (agent finding 3) | pinned `5.1.4` (peer-compatible with vite 7.1.2; npm cache fracture worked around via /tmp cache); `npm ci` + `npm run build` → ✓ dist/ | `f6f25b21` |
| P1 migration 0007 `Text` vs model `JSONB` (agent finding 5) | migration now `JSONB().with_variant(JSON,"sqlite")`; fresh-DB `alembic upgrade head` OK; orchestration tests 11/11 | `f6f25b21` |
| P1 dev compose frontend: prod nginx image on 5173, dead HMR + no migrate step (agent finding 7) | dev compose now runs node:20 + Vite dev server with `npm ci`; explicit `migrate` service gates backend; compose config OK | `f6f25b21` |
| Fatal env-template recipe: docs `cp .env.example .env` + compose-only keys → `extra="forbid"` crash (agent finding 1) | split into `.env.compose.example` + `ERP-BACKEND/.env.example`; docs updated; Settings loads from clean template | `f6f25b21` |
| Invalid `typesafe==0.1.0` pin → `0.9.1` | dev-deps install OK | `7f1126ee` |
| Idempotency conflict codes typed (no message sniffing) | full suite 48 passed / 1 PG-skip | `7f1126ee` |
| `frontend/node_modules/` ignored; lockfile tracked | `git status` clean | `e1a507c4` |
| Startup-failure root cause (null `pull_request.number`) | zero references; `runs-on: ubuntu-latest` everywhere | prior |
| IaC workflow restored with safe concurrency | `.github/workflows/iac.yml` present | `8e56739d` |
| tracker: agent finding 4 (compose sqlite default) duplicates ENV-1 row → superseded by `73ecc902` | — | `73ecc902` |
| P1 FE-1: `VITE_API_BASE_URL` runtime-env no-op (agent finding 6) | Dockerfile `ARG` in build stage; compose `build.args` `${VITE_API_BASE_URL:-/api}`; `App.jsx` fallback removed; nginx `/api/`→`backend:8000/api/v1/` verified | `6883b400` |
| P1 METRICS-1: `/metrics` unauthenticated (agent finding 10) | ASGI Bearer-JWT auth in `app/core/metrics.py`; no-auth 401 / invalid 401 / valid 200; +3 regression tests in `tests/test_api.py`; full suite 52 passed | `6883b400` |
| P1 TS-2: legacy fingerprint-less replay semantics (agent finding 9) | `transaction_store.py` raises `IDEMPOTENCY_KEY_REUSED` on fingerprint-less replay; seeded-legacy-row test passes | `6883b400` |
| P1 QUAL-1: `qualify.sh` PG precondition probe (agent finding 13) | `probe_postgres()` + hermetic SQLite fallback present & verified in script | `6883b400` |
| P1 CI-1: frontend installs ignore lockfile (agent finding 8) | `frontend/Dockerfile` + `ci.yml:71` + `quality.yml` + `qualify.sh` all `npm ci`; lockfile `frontend/package-lock.json`; YAML validated | `6883b400` |
| Deep-dive SETP-1 (env integration): setup.sh emitted undeclared keys → `extra="forbid"` crash | corrected dev/prod backend `.env` heredocs in `setup.sh` to declared Settings fields only; corrected `DB_POOL_SIZE`/`DB_MAX_OVERFLOW`/`JWT_EXPIRY_MINUTES`; verified `Settings()` loads clean | `6883b400` |
| Code review follow-up (2026-10-30): P0-1 idempotency key overflow; P0-2 frontend privileged port; P1-1/P1-2 rate limiter hardening; P1-3 TransactionStore test isolation; P1-4 Vite dev proxy; P1-5 invoice_no parsing guard; P2 hygiene/docs/password policy | full gate green: ruff 0, format clean, compileall OK, alembic single head, 54 passed / 1 skipped | `28fce033` |
| Follow-up L3: trusted-proxy XFF resolution + 429 threshold tests for RateLimitMiddleware | 3 new tests in tests/test_rate_limiter.py; all pass | `cc786a23` |
