# Production Hardening Record

## Scope

This hardening pass focuses on the ERP03 engineering foundation: repository hygiene, secret handling, container boundaries, CI quality gates, Kubernetes runtime correctness, Terraform validation, and operational documentation.

## Verified findings from repository inspection

- `main` was unprotected at the start of the hardening pass.
- No active GitHub Actions workflow existed under `.github/workflows` on the inspected baseline.
- `.env.production` contained database credentials and an application signing secret.
- `ERP-BACKEND/.env` was committed.
- Database credential files existed under `secrets/`.
- Coverage artifacts and a local SQLite database were committed.
- The root `.gitignore` incorrectly ignored normal JavaScript/TypeScript/CSS source extensions.
- The backend image already used a multi-stage build but was pinned to Python 3.11 and copied the full build context.
- The compose stack referenced a missing `ERP-BACKEND/Dockerfile.worker`.
- The frontend Dockerfile expected `package-lock.json`, but the frontend did not contain one.
- Kubernetes API probes referenced `/health/live`, `/health/ready`, and `/health/startup`, while the FastAPI application exposed `/health` and `/api/v1/health`.
- The Kubernetes ingress routed the API to port 3000 while the API service listens on 8000.
- Kubernetes worker manifests contained Node.js health-check logic even though the worker is Python/Celery.
- Kubernetes backup CronJobs referenced AWS CLI commands from images that do not contain the AWS CLI.
- The Terraform production configuration used `random_id` without declaring the Random provider.

## Hardening implemented

- Removed committed environment and credential artifacts from the hardened branch.
- Added safe environment templates and explicit secret provisioning documentation.
- Added file-backed secret support to the backend configuration.
- Standardized bcrypt to a Passlib-compatible version.
- Hardened backend and frontend container images and non-root execution.
- Reworked Compose migration ordering into a dedicated migration service.
- Added request health/readiness semantics and Prometheus metrics validation.
- Added frontend ESLint flat configuration.
- Added CI for tests, audits, lint/build, Terraform validation and Kubernetes rendering.
- Added Dependabot configuration.
- Corrected Kubernetes probes, service ports, secret contracts, Redis authentication, ingress routing and worker runtime checks.
- Removed non-functional backup CronJobs from the production Kustomization rather than shipping an unverified backup implementation.
- Added Terraform Random provider declaration and remote-state guidance.
- Replaced stale README deployment instructions with the current operational baseline.

## Security caveat

Deleting a secret from the current branch does not erase historical Git objects or external copies. Any credential that was ever real must be rotated/revoked independently. Repository history rewriting is intentionally not performed as part of this hardening pass.

## Remaining gates before production approval

1. Run the new CI workflow to completion and remediate all dependency audit findings.
2. Generate and commit `frontend/package-lock.json`, then switch frontend CI/build from `npm install` to `npm ci`.
3. Configure GitHub branch protection/rulesets on `main`.
4. Configure a production secret manager and provision `erp_solution-secrets` in Kubernetes.
5. Configure a remote, encrypted Terraform backend with state locking.
6. Validate the Kubernetes overlay against the actual target cluster and ingress controller.
7. Perform a controlled database migration rehearsal and rollback test.
8. Configure Prometheus alerting and centralized log retention.
9. Perform an independent security review before production exposure.
