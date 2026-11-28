# Remaining Tasks – Production Readiness

## Production Readiness Matrix – Open Items

### Code quality – PASS
- Ruff/pytest gates verified locally: 0 findings, 49 passed / 1 skipped (PG-only)
- Evidence: `docs/TODO.md` Done & verified ledger

### CI/CD – AWAITING GITHUB EVIDENCE
- GitHub Actions runners switched from `ubuntu-24.04` to `ubuntu-latest` to resolve `startup_failure`
- Path filters added to all workflows
- IaC workflow restored with safe concurrency
- **Awaiting:** GitHub Actions execution evidence for current HEAD (`1f5bcbc2`)

### Security – AWAITING GITHUB EVIDENCE
- Dependency audit (pip-audit), CodeQL, container scanning (Trivy) workflows present
- Typed idempotency error codes implemented
- JWT expiry now configurable via `jwt_expiry_minutes` setting
- `/metrics` protected with bearer token auth
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
- Alembic migrations verified (single head `0007`)
- Backup verification script (`scripts/backup_verify.sh`) added
- **Awaiting:** Restore drill evidence, automated backup cron

### Release management – PASS
- SemVer release workflow + notes template + deploy runbook (`docs/DEPLOY_RUNBOOK.md`)

### Testing – PASS (local qualification passed)
- `./scripts/setup.sh --qualify` passed: 49 passed / 1 skipped, frontend build OK
- Idempotency payload mismatch vs reuse distinguished (typed error codes)

## Immediate Next Steps (GitHub-side)

1. Verify CI green on `ubuntu-latest` for current HEAD
2. Merge Priority 1 PRs: #170, Dependabot #191-196, #229, #228
3. Close resolved issues: #224, #226, #223
4. Execute release workflow and tag v1.0.1

Last update: 2026-10-20
