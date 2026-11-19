# ERP03 Deploy Runbook

**Target:** production-ready `main` at `origin/main`
**Current HEAD:** `b639c2d6` — lint/format/compile/migrations/tests green (48 passed / 1 PG-skip)

## Phase 0 — Pre-flight (local verification)

Run once before touching GitHub:

```bash
cd /home/ubuntu/ERP03
git status --short                       # must be empty
git log --oneline -1                     # b639c2d6
cd ERP-BACKEND
.venv/bin/ruff check app tests alembic   # 0 findings
.venv/bin/ruff format --check app tests alembic
.venv/bin/python -m compileall -q app alembic
.venv/bin/python -m pytest -q            # 48 passed, 1 PG-only skip
cd ../frontend
npm ci && npm run build                  # dist/ emitted
```

If any step fails, fix and push first — do not proceed.

## Phase 1 — CI evidence (GitHub Actions)

Open Actions for commit `b639c2d6` and confirm **all** green:

| Workflow | What it proves |
|---|---|
| CI | backend build + test + frontend build |
| Quality | ruff lint/format + compileall |
| Security | pip-audit + CodeQL |
| Container | image build + Trivy scan |
| IaC | terraform fmt/validate/plan + artifact |

**Entry gate:** no workflow red, no `startup_failure`, no build errors.

## Phase 2 — Issue closure

Once Phase 1 is green:

```bash
gh issue close 224 --repo nyeinpyaesone-ui/ERP03 --comment "CI runners on ubuntu-latest, path filters added, runs green."
gh issue close 226 --repo nyeinpyaesone-ui/ERP03 --comment "CI reliability verified on ubuntu-latest."
gh issue close 223 --repo nyeinpyaesone-ui/ERP03 --comment "Idempotency payload mismatch vs reuse distinguished (typed error codes, tests updated)."
```

## Phase 3 — PR merge queue (order matters)

```bash
gh pr merge 170 --repo nyeinpyaesone-ui/ERP03 --squash          # env credential rotation (security-first)
gh pr merge 191 --repo nyeinpyaesone-ui/ERP03 --squash          # Dependabot
gh pr merge 192 --repo nyeinpyaesone-ui/ERP03 --squash
gh pr merge 193 --repo nyeinpyaesone-ui/ERP03 --squash
gh pr merge 194 --repo nyeinpyaesone-ui/ERP03 --squash
gh pr merge 195 --repo nyeinpyaesone-ui/ERP03 --squash
gh pr merge 196 --repo nyeinpyaesone-ui/ERP03 --squash
gh pr merge 229 --repo nyeinpyaesone-ui/ERP03 --squash          # after CI green
gh pr merge 228 --repo nyeinpyaesone-ui/ERP03 --squash
```

Rule: do not merge any PR unless the CI run for its head commit is green.

## Phase 3b — Staging deploy

In Codespace (Docker-in-Docker):

```bash
make dev                              # docker compose -f docker-compose.dev.yml up --build
make lint && make test && make build-all
```

Verify backend healthz, frontend loads, and Trivy scan shows no NEW critical/high vs baseline.

## Phase 4 — Production readiness

After Phase 3 merges land on `main`:

1. `git fetch origin && git checkout main && git pull --ff-only`
2. Update `docs/PRODUCTION_READINESS_MATRIX.md`:
   - Code Quality → PASS (link CI run)
   - CI/CD → PASS (link CI run)
   - Testing → PASS (link pytest output)
   - Final production readiness → QUALIFIED (link staging smoke output)
3. Commit + push the matrix update.
4. Tag release: `git tag v1.0.0 && git push origin v1.0.0`
5. Create GitHub release from tag via workflow_dispatch on `release.yml`.

## Rollback

If staging smoke fails: revert the last merged PR, re-run Phase 1–3, do not tag.
