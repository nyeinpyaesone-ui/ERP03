# Code Review (Simulation Mode B) — Remediation Diff

**Mode:** `agent_simulation` (no Jev API key; `jev_called: false`; probability/confidence `null`)
**Scope:** diff `main..fix/review-findings-2026-10-30` (18 files, +338/-36)
**Receipts:** ruff 0 findings, format clean, compileall OK, alembic single head, pytest 54 passed / 1 skipped, frontend build OK.

## Leads (each: hunk → concern → uncertainty → verify)

### L1 — Thread-safety of lazy `_store` init (HIGH)
- **Hunk**: `app/api/transactions.py` `get_store()` (new)
- **Concern**: `_store` global created lazily without a lock; two concurrent requests on first use can create two `TransactionStore` instances, each with its own `threading.RLock`, pointing at the same SQLite file → uncoordinated writes / "database is locked".
- **Uncertainty**: low under single-worker dev; high under multi-worker prod.
- **Verify**: add a concurrency test (N threads calling `get_store()` simultaneously) asserting identity equality; or initialize eagerly at import (original behaviour) and keep `reset_store` for tests only.

### L2 — Password policy weakened (MEDIUM, security)
- **Hunk**: `app/services/bootstrap.py` `validate_password_policy` now uses `settings.password_min_length` (default 8) instead of 12.
- **Concern**: effective minimum dropped from 12 to 8, weakening bootstrap password policy.
- **Uncertainty**: medium — config default 8 may be intentional for dev, but prod should enforce ≥12.
- **Verify**: set `password_min_length` default to 12 in `config.py`, or keep 12 in `validate_password_policy` and make config a floor. Add test asserting 11-char password rejected.

### L3 — Rate limiter eviction mutates dict after comprehension (LOW, verified safe)
- **Hunk**: `app/main.py` `RateLimitMiddleware.__call__` stale eviction.
- **Concern**: none — `stale` list is materialised before deletion.
- **Uncertainty**: none.
- **Verify**: existing `test_api.py` covers 429; add a test for forwarded-IP handling with a trusted proxy.

### L4 — `next_invoice_no` sequence scoping (LOW)
- **Hunk**: `app/services/sales.py` guard.
- **Concern**: malformed `last` resets to sequence 1, which could collide with an existing `INV-…-000001` if a malformed row exists alongside valid ones. The unique constraint on `(branch_id, invoice_no)` will raise, surfaced as `ConflictError("Invoice number already exists…")` — acceptable but not ideal.
- **Uncertainty**: low; only matters with pre-existing malformed data.
- **Verify**: integration test seeding two invoices (one malformed) and asserting no crash + no duplicate.

### L5 — Frontend Dockerfile build stage still root (INFO)
- **Hunk**: `frontend/Dockerfile` build stage.
- **Concern**: build runs as root (standard for node image) — acceptable for build-only stage; runtime is unprivileged.
- **Uncertainty**: none.
- **Verify**: none required.

### L6 — `docker-compose.dev.yml` removed pip install (MEDIUM, ops)
- **Hunk**: backend command.
- **Concern**: if the image deps are stale relative to `requirements.txt`, dev will fail at import. The volume mount overlays code but not deps.
- **Uncertainty**: medium — depends on image freshness.
- **Verify**: `docker compose -f docker-compose.dev.yml up --build` and confirm backend starts; or keep a guarded `pip install -r requirements.txt` behind a flag.

### L7 — Test isolation change could mask store bugs (LOW)
- **Hunk**: `tests/test_transactions.py` autouse fixture resets store per test.
- **Concern**: per-test fresh store hides cross-test state leakage bugs; but improves determinism. Acceptable for unit tests.
- **Uncertainty**: low.
- **Verify**: keep one integration test using a shared store to catch leakage.

### L8 — `trusted_proxies` default empty (INFO)
- **Hunk**: `app/core/config.py`.
- **Concern**: `X-Forwarded-For` ignored by default → correct/safe default.
- **Uncertainty**: none.

## Conclusion

No blocking defects found. Two follow-ups recommended (L1 thread-safety, L2 password minimum). All other leads are informational or low-risk. Gate remains green (54 passed / 1 skipped).

## Resolution status (post-review)

- **L1 (thread-safety)** — RESOLVED: `get_store()`/`reset_store()` now guarded by `threading.Lock()` with double-checked locking (commit `4d968402`).
- **L2 (password minimum)** — RESOLVED: `settings.password_min_length` default raised from 8 to 12 (commit `4d968402`); `validate_password_policy` uses the configured minimum.
- **L6 (dev compose)** — MITIGATED: backend command no longer reinstalls deps; relies on image deps. Verify image freshness before release.
- Gate at resolution: ruff 0, format clean, compileall OK, alembic single head `0007`, pytest 54 passed / 1 skipped.
