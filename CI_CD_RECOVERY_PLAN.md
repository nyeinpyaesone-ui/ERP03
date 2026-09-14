# ERP03 CI/CD Recovery Status

## Current State

ERP03 source-side qualification hardening is implemented on `main`. Production qualification remains blocked by GitHub Actions runner allocation.

### Repository baseline

- Main HEAD: `256c44957830da61eebba6577cc4e6652f90e927`
- Qualification workflow: `.github/workflows/erp03-qualification.yml`
- Runtime baseline: Python 3.12.13, PostgreSQL 15, Redis 7
- Frontend qualification uses the committed `package-lock.json` with `npm ci`
- Production API migration ownership is externalized to the deployment gate; the API container does not run migrations during application startup
- Production Python base images are pinned to an immutable registry digest

## Blocking Gate

Issue #210 is the authoritative CI blocker.

Repeated qualification runs have terminated with `startup_failure` before GitHub creates any workflow jobs. Therefore the repository cannot obtain migration, test, lint, build, or container-build evidence from GitHub Actions until a usable GitHub-hosted or authorized self-hosted runner is available.

## Required Recovery Action

Restore or authorize a usable GitHub Actions runner for this repository, then execute the qualification workflow from `main`.

The recovery criterion is **actual job allocation**, followed by successful execution of the backend migration/tests/container builds and frontend lint/build/container build.

## Security Note

Do not store GitHub credentials, access tokens, passwords, or other authentication material in this document or in repository files. Git operations requiring authentication must use the GitHub credential mechanism appropriate to the execution environment.

## Release Rule

A successful source build is not sufficient for production qualification. Do not publish or label ERP03 `v1.0.0` production-ready until the release-gate evidence exists for CI execution, runtime behavior, security/secrets, deployment, recovery, and client UAT.
