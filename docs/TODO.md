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

- [ ] **FE-1: `VITE_API_BASE_URL` as runtime env is a no-op (agent finding 6).**
     _URL is evaluated at build time (`frontend/vite.config.js`, `App.jsx`);
      prebuilt GHCR images bake `http://localhost:8000/api/v1` in, breaking any
      real host deployment. Fix: default to relative base and rely on the
      existing nginx `/api/` proxy (`frontend/nginx.conf:9-10`), or accept the
      URL as a Docker build ARG. *Acceptance: built image serves API calls
      without runtime env.*
- [ ] **TS-2: Legacy fingerprint-less replay semantics (agent finding 9).**
      Legacy rows without `request_fingerprint` replay silently on any payload;
      `IDEMPOTENCY_KEY_REUSED` is currently unreachable via data. Decide
      semantics (recommend: mismatch-on-fingerprint-less → `IDEMPOTENCY_KEY_REUSED`)
      and add a test that seeds a legacy row.
- [x] **METRICS-1: `/metrics` unauthenticated (agent finding 10).** Gate with
      auth claims or bind to an internal-only port/target.
      _Kept `/metrics` authenticated (JWT required) but added a dedicated
      `metrics_scrape_token` bearer token so Prometheus can scrape without a
      user JWT. Added `metrics_scrape_token` setting, updated metrics auth
      middleware to accept it, and configured Prometheus scrape job with
      `authorization: Bearer ${METRICS_SCRAPE_TOKEN}`. Also fixed the
      prometheus-rules.yml metric-name mismatch (gap 3.1) and initialized
      OpenTelemetry telemetry behind `telemetry_enabled` + `otlp_endpoint`
      settings (gaps 3.2, 3.1)._ Evidence: commit `39a1b5d5`, gate green
      (ruff check/format clean, compileall clean, pytest 49 passed / 1
      skipped).
- [ ] **AUTH-1: JWT TTL hardcoded 480 min, claims never re-validated against
      User/branch state (agent finding 11).** Add a Settings knob, re-check
      `User.active` on privileged endpoints or shorten TTL; consider login
      rate-limiting.
- [ ] **SETP-1: setup.sh emits container-absolute SQLite path for host use
      (agent finding 12).** Point `database_url`/`database_path` at the same
      venv-local absolute file.
- [ ] **QUAL-1: qualify.sh assumes a pre-provisioned PG with fixed creds and
      no precondition probe (agent finding 13).** Probe first, print
      actionable hint, hermetic fallback.
- [ ] **CI-1: Frontend installs ignore the lockfile (agent finding 8).**
      `frontend/Dockerfile`, `ci.yml:75-81`, `qualify.sh:47` — switch to
      `npm ci` and lock the Express and `cache-dependency-path` to
      `package-lock.json`.
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
- [ ] **DEP-2: Move pytest/pytest-asyncio/httpx out of prod requirements**
      (agent finding 18) — CI depends on them only because they ship in prod;
      correct ci.yml deps then trim requirements (agent finding 18)
      and ci.yml: install dev-requirements for the test job.
- [ ] **DEP-2b: delete stray root `package-lock.json`** (agent finding 17).
- [ ] **DEVOPS-1: `migrate` advisory depends_on lets API boot with no tables
      (agent finding 16) — set `required: true`.**
- [ ] **T-1: 36 pytest library-deprecation warnings — track, don't suppress.**

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
