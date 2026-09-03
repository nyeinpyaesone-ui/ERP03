# ERP03 Production Readiness — Implementation Baseline

Date: 2026-08-11
Base: `main` at `a95a8db828d02c3a7d37e5f649478a1865fe3b13`

## Verified repository facts

- Default branch: `main`
- Repository visibility: public
- Primary application directories include `backend/`, `frontend/`, `mobile/`, `infra/`, and `docker/`.
- Multiple historical application trees are present: `backend-v1.8/` and `backend-v2.1/` in addition to `backend/`.
- Root `backend/README.md` identifies the active backend as ERP erpo3 System v2.2 and describes FastAPI + SQLAlchemy + PostgreSQL, Alembic migrations, Redis, Ollama, WebSockets, workflows, integrations, and RBAC.
- Docker assets exist for API, worker, web, and compose-based deployments.
- Kubernetes assets exist under `infra/k8s/`.
- No Terraform/OpenTofu structure was identified during this baseline inspection.

## Critical findings

### 1. Authoritative application tree

`backend/` is the strongest candidate for the current application because its README identifies v2.2 and the root deployment files use `backend/` as the build context. Historical trees must not be deployed by CI until explicitly retired or documented as archived.

### 2. Existing CI/CD is build-and-push, not a complete release pipeline

The previous workflow logged into Docker Hub and pushed backend/frontend images from `main` and version tags. It did not provide the required pre-merge quality gates, integration validation, security gates, staging promotion, or production approval flow.

### 3. Production Compose contains unsafe defaults

`docker-compose.prod.yml` currently exposes PostgreSQL and Redis ports, uses fallback passwords such as `changeme`, uses a fallback application secret, uses floating `latest` image tags, and uses a floating `ollama/ollama:latest` image. These defaults must be removed before production deployment.

### 4. Backend image needs hardening

`backend/Dockerfile` currently uses `python:3.11-slim`, installs build tooling into the runtime image, runs as the default user, has no container healthcheck, and does not use a multi-stage build. These are hardening tasks, not yet production-complete items.

### 5. Testing evidence is insufficient

A Makefile advertises `make test`, but the repository baseline does not yet establish a reliable CI test contract or minimum coverage threshold. The new CI foundation therefore deliberately starts with deterministic syntax/build validation rather than pretending a full test suite already exists.

## Implementation sequence

1. Establish repository/application baseline.
2. Add non-destructive PR quality/build gates.
3. Make container builds reproducible and hardened.
4. Add dependency and container security scanning.
5. Establish integration/smoke tests against an isolated environment.
6. Replace mutable production image references with immutable release digests/tags.
7. Add staging deployment and verification.
8. Add production promotion with explicit approval.
9. Add rollback, backup/restore, observability and operational validation.
10. Only then declare production readiness.

## Explicit non-actions in this phase

- No production deployment was triggered.
- No secrets were created or changed.
- No Docker Hub credentials were modified.
- No historical backend tree was deleted.
- No Kubernetes production resources were applied.
- No database migration was executed.

## Acceptance rule

A checklist item is considered complete only when repository evidence and an executable validation step prove it. Documentation claiming completion is not treated as proof by itself.
