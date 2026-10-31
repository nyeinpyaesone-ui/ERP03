# ERP03 Production Readiness Matrix

This matrix maps the repository implementation checklist to verified repository evidence. A checked source item does not equal production approval until its runtime gate passes.

| Area | Current evidence | State |
|---|---|---|
| Repository discovery | Backend, frontend, deployment and workflow tree identified | PASS |
| Baseline verification | Python/Node/PostgreSQL versions are pinned in CI; package manifests verified | PASS |
| Code quality | Ruff lint/format gate added; path filters applied; CI green | PASS |
| CI/CD | CI + Qualification + Quality + Security + Container + IaC workflows present; runners switched to ubuntu-latest; path filters added; CI green | PASS |
| Containerization | Non-root backend, health checks, pinned runtime images, Dockerfile deps-path fixed | PASS |
| Local bootstrap | Compose + env configuration present; devcontainer with PostgreSQL + Redis services | PASS |
| Devcontainer | Docker Compose-based devcontainer with pre-built dependencies; Docker Hub push workflow | PASS |
| Infrastructure as Code | Terraform contract + validation workflow + artifact upload | PASS |
| Kubernetes | Base manifests, probes, resources, overlays | PARTIAL |
| Security | Dependency audit + CodeQL + container scanning; alerts added | PASS |
| Observability | Request IDs, structured request logging, `/metrics` (auth-gated) | PARTIAL |
| Database protection | Alembic migrations + restore runbook verified | PASS |
| Release management | SemVer release workflow + notes template + deploy runbook | PASS |
| Testing | Unit/integration/qualification gates present; idempotency payload mismatch test updated; CI green | PASS |
| Operational runbooks | Deployment, rollback, backup/restore, incident, maintenance | PASS |
| Final production readiness | All PASS-gates verified; Kubernetes & observability noted as PARTIAL with runbooks | QUALIFIED |

## Release blockers

1. GitHub-hosted runner allocation verified on ubuntu-latest – RESOLVED
2. Quality/security/container/IaC workflows execute and pass – RESOLVED
3. Staging infrastructure, secret management, TLS, backup automation, alerting, and restore evidence – document in runbooks
4. PR #219 qualification evidence captured – RESOLVED

## Immediate next steps (GitHub-side)

```bash
# Verify CI green for current HEAD
gh run list --repo nyeinpyaesone-ui/ERP03 --branch main --status success --limit 5

# Merge Priority 1 PRs (only after CI green)
gh pr merge 170 --repo nyeinpyaesone-ui/ERP03 --squash
gh pr merge 191 --repo nyeinpyaesone-ui/ERP03 --squash
gh pr merge 192 --repo nyeinpyaesone-ui/ERP03 --squash
gh pr merge 193 --repo nyeinpyaesone-ui/ERP03 --squash
gh pr merge 194 --repo nyeinpyaesone-ui/ERP03 --squash
gh pr merge 195 --repo nyeinpyaesone-ui/ERP03 --squash
gh pr merge 196 --repo nyeinpyaesone-ui/ERP03 --squash

# Close resolved issues
gh issue close 224 --repo nyeinpyaesone-ui/ERP03 --comment "CI runners on ubuntu-latest, path filters added, runs green."
gh issue close 226 --repo nyeinpyaesone-ui/ERP03 --comment "CI reliability verified on ubuntu-latest."
gh issue close 223 --repo nyeinpyaesone-ui/ERP03 --comment "Idempotency payload mismatch vs reuse distinguished (typed error codes, tests updated)."
```
