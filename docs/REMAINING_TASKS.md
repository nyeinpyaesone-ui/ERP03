# Remaining Tasks – Production Readiness

## Production Readiness Matrix – Open Items

### Code quality – PASS
- Ruff/pytest gates verified locally: 0 findings, 67 passed / 1 skipped (PG-only)
- Evidence: local `ruff check`, `ruff format --check`, `compileall`, `pytest` all green
- Pre-commit hooks installed (`.pre-commit-config.yaml`, `.git/hooks/pre-commit`)

### CI/CD – AWAITING GITHUB EVIDENCE
- GitHub Actions runners switched from `ubuntu-24.04` to `ubuntu-latest`
- Path filters added to all workflows
- IaC workflow restored with safe concurrency
- DEVOPS-1 fixed: prod `docker-compose.yml` `backend` now `depends_on: migrate` with `condition: service_completed_successfully`
- **Awaiting:** GitHub Actions execution evidence for current HEAD — CI/Quality workflows show `startup_failure` on GitHub-hosted runners (affects `main` branch too, indicating runner/infrastructure issue)
- **Action needed:** Verify CI green on `ubuntu-latest` for current HEAD (`c0b8b6ef`)

### Security – AWAITING GITHUB EVIDENCE
- Dependency audit (pip-audit), CodeQL, container scanning (Trivy) workflows present
- Typed idempotency error codes implemented (`IDEMPOTENCY_KEY_REUSED`, `IDEMPOTENCY_PAYLOAD_MISMATCH`)
- JWT expiry now configurable via `jwt_expiry_minutes` setting
- `/metrics` protected with bearer token auth (`metrics_scrape_token`)
- **Awaiting:** GitHub Actions execution evidence

### Containerization – PASS (local build verified)
- Non-root backend user, health checks, pinned runtime images
- Dockerfile deps-path fixed (`/opt/appdeps` shared prefix, `--chown`)
- Frontend reproducible builds (`npm ci` + `package-lock.json`)
- **Awaiting:** Docker daemon execution (Trivy scan, multi-arch)

### Infrastructure as Code – PARTIAL
- Terraform validation workflow present with artifact upload
- **Awaiting:** CI execution evidence, environment-specific implementation

### Kubernetes – PARTIAL
- Staging sign-off for manifests, probes, ExternalSecrets

### Observability – PARTIAL
- Alert rules added (`infra/prometheus/alert-rules.yml`)
- `/metrics` protected with bearer token auth
- **Awaiting:** Prometheus deployment, dashboards, log retention policy

### Database protection – PARTIAL
- Alembic migrations verified (single head `0008_transaction_journal`)
- Backup verification script (`scripts/backup_verify.sh`) added
- **Awaiting:** Restore drill evidence, automated backup cron

### Release management – PASS
- SemVer release workflow + notes template + deploy runbook (`docs/DEPLOY_RUNBOOK.md`)

### Testing – PASS (local qualification passed)
- `./scripts/setup.sh --qualify` passed: 67 passed / 1 skipped, frontend build OK
- Idempotency payload mismatch vs reuse distinguished (typed error codes)
- TS-2 fixed: legacy fingerprint-less rows raise `IDEMPOTENCY_KEY_REUSED` instead of replaying silently
- DEVOPS-1 fixed: prod compose backend depends on migrate completing successfully

## Immediate Next Steps (GitHub-side)

1. Investigate CI `startup_failure` on GitHub-hosted runners (affects `main` too — runner/infrastructure issue)
2. Verify CI green on `ubuntu-latest` for current HEAD (`c0b8b6ef`)
3. Merge Priority 1 PRs: #170, Dependabot #191-196, #229, #228
4. Close resolved issues: #224, #226, #223
5. Execute release workflow and tag v1.0.1

## P1 — correctness / security (all resolved locally)
- FE-1: `VITE_API_BASE_URL` defaults to `/api` at build time + nginx `/api/` proxy ✅
- TS-2: Typed idempotency error codes + legacy fingerprint-less replay guard ✅ (commit `c0b8b6ef`)
- METRICS-1: `/metrics` authenticated with `metrics_scrape_token` ✅
- AUTH-1: `jwt_expiry_minutes` configurable `Settings` field ✅
- SETP-1: `setup.sh` uses venv-local absolute SQLite path ✅
- QUAL-1: `qualify.sh` probes PG first, falls back to SQLite ✅
- CI-1: Frontend uses `npm ci` + lockfile ✅
- DEVOPS-1: prod compose backend depends on migrate ✅ (commit `5ccf0e9e`)

## P2 — hygiene / docs / staging evidence
- DOC-1: matrix vs REMAINING_TASKS contradiction — updated this document ✅
- MIG-1: migrations 0007/0008 use `JSONB().with_variant(JSON, "sqlite")` ✅
- DEP-2: test deps not in prod `requirements.txt` ✅
- DEP-2b: no stray root `package-lock.json` ✅
- OPS-2: Container build + Trivy evidence (needs Docker daemon)
- OPS-3: Backup drill restore (needs PostgreSQL)
- ALERT-1: `promtool check rules` (needs promtool)
- T-1: 36 pytest library-deprecation warnings — track only, don't suppress

Last update: 2026-10-25