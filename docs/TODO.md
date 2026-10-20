# ERP03 Remediation Tracker

**Updated:** 2026-10-20 · **Source:** live verification session + full-repo scan
**Supersedes the task lists in** `REMAINING_TASKS.md` (kept for history).

## How to work this list (methodology)

Every item follows the same loop — no exceptions:

1. **Branch** from latest `origin/main` (`fix/<topic>` or `chore/<topic>`).
2. **Reproduce / evidence** the problem first (command + output recorded below).
3. **Fix minimally** — one logical change per commit, conventional-commit message.
4. **Verify with the mandatory gate:**

   ```bash
   cd ERP-BACKEND
   .venv/bin/ruff check app tests alembic
   .venv/bin/ruff format --check app tests alembic
   .venv/bin/python -m compileall -q app alembic
   .venv/bin/alembic heads                     # must be exactly one head
   .venv/bin/alembic upgrade head              # all migrations apply (SQLite)
   .venv/bin/python -m pytest -q               # target: 0 failed; PG-only skips allowed
   ```

5. **Record evidence** (commit SHA + command output summary) in this file.
6. **Move item to "Done & verified"** with its SHA.

Severity: **P0** = blocks startup/CI or breaks a client-visible contract · **P1** = correctness/security with workaround · **P2** = hygiene, docs, warnings.

---

## P0 — blocking / contract-breaking

- [ ] **ENV-1: Compose↔Settings contract audit.** With `extra="forbid"` in
      `Settings`, any env var referenced by `docker-compose*.yml` or
      `.env.example` that is not a declared Settings field makes the process
      crash at startup. Enumerate every env var in both files, diff them
      against `app/core/config.py` field names, and fix the mismatched ones.
      *Acceptance:* `docker compose -f docker-compose.dev.yml config` passes AND
      `python -c "from app.core.config import Settings; Settings()"` succeeds
      with the same env vars exported.
- [ ] **OPS-1: CI green evidence on `ubuntu-latest`.** Confirm the latest run
      fur commit `7f1126ee` is green for CI/Quality/Security/Container/IaC.
      If any workflow still fails on the platform, paste the run URL + failing
      step before switching anything.
- [ ] **PR-1: Merge queue.** After OPS-1 goes green: #170 (env credential
      rotation), then Dependabot #191–#196, then #229/#228/#220. Rebase any
      stale PR branch onto `7f1126ee` before merging.

## P1 — correctness / security

- [ ] **SEC-1: JWT key material.** HS256 with shared secret is accepted for a
      single-cluster monolith (see `docs/CODE_REVIEW.md` LOW note). Item: keep a
      checklist step to move to RS256 *when* a second verifier appears; until
      then verify `SECRET_KEY` rotation runbook exists.
- [ ] **DB-1: SQLAlchemy pool parity.** Ensure the engine setup consumes the
      auto-tuned Settings pool fields and enables
      `pool_pre_ping=True` so a restarted Postgres is not served stale
      connections. *Acceptance:* grep-proves the engine kwargs and a pytest run.
- [ ] **SALES-1: Fingerprint conflict typing.** Verify `services/sales.py`
      raises the typed conflict (no message-sniffing anywhere: `grep -rn
      "in msg" app/` must return nothing).
- [ ] **T-1: Warning triage.** 36 pytest warnings are library deprecations
      (Starlette/anyio/pydantic). File/upgrade per pip-audit output; do not
      blanket-suppress. *Acceptance:* warnings either gone or tracked with
      issue links in this file.

## P2 — hygiene / docs / staging evidence

- [ ] **DOC-1:** Reconcile `PRODUCTION_READINESS_MATRIX.md` statements with
      live evidence; any claim without a commit/run reference gets the SHA.
- [ ] **OPS-2: Container build evidence.** `make build-backend` /
      `build-frontend` require a Docker daemon; capture image build + Trivy
      scan evidence in Codespace (Docker-in-Docker) and link the run here.
- [ ] **OPS-3: Backup drill.** Run `scripts/backup_verify.sh` once against a
      real staging DB with `BACKUP_DIR` mounted; record the SHA-256 + restore
      dry-run output in the runbook.
- [ ] **ALERT-1:** Load `infra/prometheus/alert-rules.yml` into a staging
      Prometheus at least once and confirm the rules parse (`promtool check
      rules`) — metric names must match what `/metrics` exports.

---

## Done & verified (this session, origin/main HEAD `7f1126ee`)

| Item | Evidence | Commit |
|---|---|---|
| Invalid `typesafe==0.1.0` pin → `0.9.1`; dev-deps install now succeeds | `pip install -r dev-requirements.txt` OK, ruff 0.17.1 | `7f1126ee` |
| Idempotency conflict codes typed (no message sniffing) | `tests/test_transactions.py:266` passes; full suite 48 passed / 1 PG-skip | `7f1126ee` |
| `frontend/node_modules/` ignored; `package-lock.json` tracked | `git status` clean | `e1a507c4` |
| Startup-failure root cause (null `pull_request.number` concurrency) | grep: zero references; `runs-on: ubuntu-latest` everywhere | prior commits |
| IaC workflow restored with safe concurrency | `.github/workflows/iac.yml` present, artifact upload | `8e56739d` |
| Full-repo quality gate green | lint/format/compileall/heads/migrations/pytest all pass live | — |
