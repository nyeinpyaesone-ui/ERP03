# ERP03 Production Qualification Gate

## Purpose
This file is an evidence-based release gate. Documentation or planned infrastructure is not treated as implemented capability.

## Mandatory gates

- [ ] No tracked secrets or real environment files.
- [ ] No tracked runtime/build artifacts (`node_modules`, `__pycache__`, `*.pyc`, coverage output).
- [ ] Dependency manifests and lockfiles are authoritative and reproducible.
- [ ] Backend, frontend, worker and database paths build successfully from a clean checkout.
- [ ] Database migrations apply from a clean database and are verified against the actual schema.
- [ ] Automated unit/integration tests pass.
- [ ] Container images build from repository sources without local-only files.
- [ ] Production deployment workflow succeeds against the actual target environment.
- [ ] Health/readiness checks verify real dependencies, not mocked services.
- [ ] Secrets are supplied through the deployment secret store; no defaults are accepted in production.
- [ ] Backup and restore are tested against the actual production database engine.
- [ ] Observability covers application errors, infrastructure health and critical business transactions.
- [ ] Rollback is validated for application artifacts and database changes; destructive database downgrade is not assumed safe.

## Current qualification result

**NOT QUALIFIED FOR PRODUCTION** until every mandatory gate is evidenced by CI or an auditable deployment test.

## Security remediation required

A tracked `.env.production` file contained production-looking database credentials and a JWT secret. Those values must be treated as compromised and rotated in the real deployment environment. Removing the file from the current branch does not erase it from Git history.

A tracked backend `.env` and coverage artifact were also removed from the qualification branch.

## Release rule

A green documentation checklist alone cannot qualify ERP03. The release candidate must demonstrate the gates above using the actual repository, actual build artifacts, actual database, and actual deployment target.
