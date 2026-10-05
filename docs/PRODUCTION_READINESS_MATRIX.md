# ERP03 Production Readiness Matrix

This matrix maps the repository implementation checklist to verified repository evidence. A checked source item does not equal production approval until its runtime gate passes.

| Area | Current evidence | State |
|---|---|---|
| Repository discovery | Backend, frontend, deployment and workflow tree identified | PASS |
| Baseline verification | Python/Node/PostgreSQL versions are pinned in CI; package manifests verified | PASS |
| Code quality | Ruff lint/format gate added | EXECUTION PENDING |
| CI/CD | CI + Qualification + Quality + Security + Container + IaC workflows present | EXECUTION PENDING |
| Containerization | Non-root backend, health checks, pinned runtime images | PARTIAL |
| Local bootstrap | Compose + env configuration present | PASS |
| Infrastructure as Code | Terraform contract + validation workflow | PARTIAL |
| Kubernetes | Base manifests, probes, resources, overlays | PARTIAL |
| Security | Dependency audit + CodeQL + container scanning | EXECUTION PENDING |
| Observability | Request IDs, structured request logging, `/metrics` | PARTIAL |
| Database protection | Alembic migrations + restore runbook | PARTIAL |
| Release management | Manual SemVer release workflow + notes template | PARTIAL |
| Testing | Unit/integration/qualification gates present | EXECUTION PENDING |
| Operational runbooks | Deployment, rollback, backup/restore, incident, maintenance | PASS |
| Final production readiness | Requires all runtime gates and staging sign-off | NOT QUALIFIED |

## Release blockers

1. GitHub-hosted runner allocation must succeed; recent runs ended in `startup_failure` with zero jobs.
2. New quality/security/container/IaC workflows must execute and pass.
3. Staging infrastructure, secret management, TLS, backup automation, alerting, and restore evidence require environment-specific implementation.
4. PR #219 must not be merged as "100% qualified" until the live qualification evidence passes.
