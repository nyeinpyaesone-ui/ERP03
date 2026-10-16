# ERP03 Production Readiness Matrix

This matrix maps the implementation checklist to repository evidence. A checked
item is repository evidence, not production approval — approval requires the
runtime gate to pass in GitHub Actions with live infrastructure.

| Area | Evidence in this repository | State |
|---|---|---|
| Repository discovery | Backend (`ERP-BACKEND`), frontend (`frontend`), infra (`infra/`), CI (`.github/workflows`, 10 workflows), docs (`docs/`) | PASS |
| Baseline verification | Python 3.12.13 / Node 22 pinned in CI; `frontend/package-lock.json` committed and `npm ci` used everywhere; dependency sets resolvable | PASS |
| Code quality | Ruff (lint + format), ESLint flat config, Prettier, shellcheck; `Makefile` targets mirror the gates | PASS (repo-clean) |
| CI/CD | CI, Quality, Security, Container, IaC, Qualification, Release, Deploy Staging, Deploy Production, Rollback | CONFIGURED |
| Containerization | Multi-stage backend, non-root runtime for backend and frontend, digest-pinned bases, health checks, `.dockerignore`, Trivy gate | PASS |
| Local bootstrap | `docker compose` with health-gated ordering, root `.env.example`, `Makefile`, documented start/stop | PASS |
| Infrastructure as Code | Provider-neutral Terraform: networking/compute/database/monitoring module contracts + dev/staging/production roots, remote-state contract, fmt/validate/plan gate | PASS |
| Kubernetes | Base manifests, dev/staging/production overlays, probes, resources, default-deny NetworkPolicies, TLS ingress, stateful components with PVCs, secret template | PASS |
| Security | gitleaks secret scan, pip-audit, npm audit, CodeQL, Trivy image scan, digest-pinned actions, least-privilege workflow permissions, RBAC-aligned NetworkPolicies | PASS (repo-clean) |
| Observability | `/healthz`, `/readyz`, `/metrics`, request IDs in logs and responses, Prometheus scrape config, 8 alert rules, Grafana dashboard | PASS |
| Database protection | Alembic single-head migrations, `scripts/backup.sh` (checksummed + encrypted), `scripts/restore-test.sh`, retention policy | PASS (repo-clean) |
| Release management | SemVer + RC tags, gate-checked release workflow, release notes template, hotfix path documented | PASS |
| Testing | 23 backend tests, coverage gate (`--cov-fail-under`), integration tests, `scripts/smoke.sh`, pre-merge and pre-release gates | PASS (repo-clean) |
| Operational runbooks | Deployment, rollback, backup/restore, incident response, maintenance checklist, release process | PASS |
| Final production readiness | Requires green pipelines, live staging sign-off and a verified restore | NOT QUALIFIED |

## Repository defects fixed in this pass

1. `celery[redis]==5.5.3` was incompatible with `redis==6.4.0`; every
   `pip install` in CI failed to resolve. Celery moved to 5.6.3.
2. Alembic had two heads (`0004_invoice_idempotency`, `0004_sales_permission`),
   so `alembic upgrade head` failed in CI, `scripts/qualify.sh` and the compose
   migrate service. Added merge revision `0005_merge_heads`.
3. `pytest` could not import `app` (no `pythonpath`), failing the whole backend
   suite at collection. Added `pythonpath = .` to `ERP-BACKEND/pytest.ini`.
4. `POST /api/v1/transactions` referenced an undefined `claims` variable — an
   authenticated idempotent transaction returned HTTP 500. The handler now
   depends on `current_claims`.
5. Overpayment was only rejected inside an open database transaction; it is
   now rejected before the transaction when all lines carry explicit prices.
6. Frontend had no lockfile, no linter and no formatter; `npm ci` in CI could
   not run. Added `package-lock.json`, ESLint and Prettier.
7. Frontend nginx listened on 80 as root and hardcoded the compose service name
   `backend`, which cannot resolve in Kubernetes. Nginx now runs unprivileged on
   8080 with a `${BACKEND_UPSTREAM}` template.
8. Workflows used tag-pinned third-party actions that this repository's own
   Actions policy rejects. All actions are now pinned to full commit SHAs and
   limited to GitHub-owned actions.
9. `iac.yml` referenced `infra/kubernetes/overlays/{dev,staging,production}`
   which did not exist, so the IaC gate could never pass.

## Remaining external blockers

1. GitHub-hosted runners must actually allocate: every workflow run since
   2026-09-17 ended in `startup_failure` with zero jobs. The repository-side
   causes (unpinned and disallowed actions) are fixed by this pass; re-run the
   workflows after pushing to confirm runner allocation.
2. Environment secrets must be configured before any deployment:
   `KUBE_CONFIG_STAGING`, `KUBE_CONFIG_PRODUCTION`, and the `erp03-secrets`
   Secret in each namespace (see `infra/kubernetes/base/secret.example.yaml`).
3. Staging and production infrastructure must exist before the deploy
   workflows can run: Kubernetes namespaces, ingress controller, cert-manager,
   Prometheus and the object storage used for backups.
4. A verified restore has not yet been executed against live infrastructure;
   `scripts/restore-test.sh` is the gate.
