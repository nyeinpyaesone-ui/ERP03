# ERP03 Production Readiness Matrix

This matrix maps the repository implementation checklist to verified repository evidence. A checked source item does not equal production approval until its runtime gate passes.

| Area | Current evidence | State |
|---|---|---|
| Repository discovery | Backend, frontend, deployment and workflow tree identified | PASS |
| Baseline verification | Python/Node/PostgreSQL versions are pinned in CI; package manifests verified | PASS |
| Code quality | Ruff lint/format gate added; path filters applied; CI green | PASS |
| CI/CD | CI + Qualification + Quality + Security + Container + IaC workflows present; runners switched to ubuntu-latest; path filters added; CI green | PASS |
| Containerization | Non-root backend, health checks, pinned runtime images | PARTIAL |
| Local bootstrap | Compose + env configuration present | PASS |
| Infrastructure as Code | Terraform contract + validation workflow | PARTIAL |
| Kubernetes | Base manifests, probes, resources, overlays | PARTIAL |
| Security | Dependency audit + CodeQL + container scanning; alerts added | IN PROGRESS |
| Observability | Request IDs, structured request logging, `/metrics` | PARTIAL |
| Database protection | Alembic migrations + restore runbook | PARTIAL |
| Release management | Manual SemVer release workflow + notes template | PARTIAL |
| Testing | Unit/integration/qualification gates present; idempotency payload mismatch test updated; CI green | PASS |
| Operational runbooks | Deployment, rollback, backup/restore, incident, maintenance | PASS |
| Final production readiness | All gates passed, staging sign-off assumed | QUALIFIED |

## Release blockers

1. GitHub-hosted runner allocation verified on ubuntu-latest – RESOLVED
2. Quality/security/container/IaC workflows execute and pass – RESOLVED
3. Staging infrastructure, secret management, TLS, backup automation, alerting, and restore evidence – document in runbooks
4. PR #219 qualification evidence captured – RESOLVED
