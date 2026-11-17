# ERP03 Production Readiness Matrix

**Audited source:** `main` at `1b32c53b414b03412a0263e22071cb8a4ac5191b` (2026-11-17).  
**Detailed evidence:** [IMPLEMENTATION_EVIDENCE_AUDIT_2026-11-17.md](IMPLEMENTATION_EVIDENCE_AUDIT_2026-11-17.md).

A source file or workflow being present is not proof that its runtime control is active. Production approval requires reproducible staging evidence.

| Area | Repository evidence | State |
|---|---|---|
| Repository discovery | Backend, frontend, infra, tests, workflows, docs and Dev Container identified | PASS |
| Baseline verification | Python/backend requirements, frontend manifest/lockfile, Dockerfiles and Compose present | PARTIAL — reconcile exact frontend versions and docs |
| Code quality | Ruff/mypy config; Quality and Type Check workflows | PARTIAL — frontend lint/type-check gates not evidenced |
| CI/CD | CI, Quality, Type Check, Coverage, Security, Container, Docker, IaC, staging, production and release workflows | PARTIAL — current main Policy Enforcement startup failure; IaC startup failure on preceding SHA; security evidence not on audited SHA |
| Containerization | Multi-stage, non-root runtime images and health checks | PARTIAL — base images not digest-pinned; Kubernetes digest placeholders remain |
| Local development | Compose, Dev Container, PostgreSQL/Redis and environment examples | PARTIAL — clean-machine end-to-end startup not verified; object storage not evidenced |
| Infrastructure as Code | Terraform contract and validation workflow | PARTIAL — no provider modules, remote state or environment-specific infrastructure |
| Kubernetes | Base resources, overlays, probes, resources, PVCs, RBAC and NetworkPolicies | PARTIAL — image digest placeholders, namespace rendering and stateful-service design require validation |
| Security | Dependency/code/container scan workflows, RBAC, NetworkPolicies, TLS template and Secret example | PARTIAL — secret manager, live TLS and exact-release scan evidence not verified |
| Observability | Health/readiness, metrics, Prometheus and OTEL configuration | PARTIAL — no Grafana dashboards found; exporter discovery and alert delivery not verified |
| Database protection | Alembic migrations and backup/restore runbooks | PARTIAL — scheduled encrypted off-host backups and restore drill not evidenced |
| Release management | Release workflow, notes template and runbooks | PARTIAL — immutable digest promotion and staging rollback drill not evidenced |
| Testing | Backend unit/integration tests, CI and coverage workflows | PARTIAL — latest main CI/coverage passed; release-grade smoke and minimum coverage policy require confirmation |
| Operational runbooks | Deployment, incident, rollback, backup/restore and maintenance docs | PARTIAL — operator rehearsals not evidenced |
| Final production readiness | Source configuration exists, but runtime gates remain outstanding | **NOT QUALIFIED** |

## Current GitHub Actions evidence

For audited main SHA `1b32c53b414b03412a0263e22071cb8a4ac5191b`:

- PASS: Quality #446, Type Check #275, CI #790, Container #328, Docker #232, Coverage #222, Agent Parity #232.
- BLOCKED: Policy Enforcement #281 — `startup_failure`, no job execution.
- Security #606 and CodeQL Setup #98 passed on preceding SHA `c3cdcca4bcee786ca38f2cbc5ef01dc60de616a8`; they are not current-SHA security evidence.
- IaC #86 ended `startup_failure` on that preceding SHA; rerun/validation on current main remains outstanding.

## Release blockers

1. Resolve/diagnose GitHub Actions startup failures without weakening policy enforcement.
2. Validate Kustomize overlays and replace every image digest placeholder with a verified immutable digest before deployment.
3. Implement provider-specific IaC and remote state only after provider/account/network decisions are confirmed.
4. Configure production secret management and TLS.
5. Deploy and verify Prometheus, exporters, Grafana dashboards and Alertmanager delivery.
6. Automate encrypted off-host backups and complete an isolated restore drill.
7. Complete staging smoke, rollback and exact-image promotion evidence.

## Production approval rule

Do not mark ERP03 production-qualified or promote a production release until all blockers have recorded evidence for the exact release candidate. No production deployment, infrastructure apply, database mutation or secret change is authorized by this matrix.
