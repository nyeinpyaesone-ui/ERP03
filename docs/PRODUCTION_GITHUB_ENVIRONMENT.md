# Production GitHub Environment Contract

ERP03 production deployment requires a protected GitHub Environment named `production`.

## Required environment secrets

- `DEPLOY_HOST` — production deployment server hostname or IP
- `DEPLOY_USER` — least-privilege deployment account
- `DEPLOY_PATH` — absolute application deployment directory
- `DEPLOY_SSH_PRIVATE_KEY` — dedicated deployment SSH private key
- `GHCR_USERNAME` — GitHub Container Registry username
- `GHCR_TOKEN` — least-privilege GitHub Container Registry token

## Protection

Configure `production` with at least one required reviewer before allowing deployment jobs to run. Restrict deployment branches/tags to the release policy used by the production workflow.

## Security requirements

1. Never commit any of the values above to the repository.
2. Use a dedicated deployment account and SSH key; do not use a personal administrator key.
3. Grant the GHCR token only the permissions required to pull the ERP03 production images.
4. Rotate deployment credentials periodically and immediately after suspected exposure.
5. Keep production credentials scoped to the `production` Environment rather than repository-wide secrets where possible.
6. Use immutable release tags/digests for production; do not deploy `latest`.

## Deployment contract

The production workflow consumes these secrets and performs the controlled release on the target server. The deployment server must have Docker Engine and Docker Compose available and must provide the production Compose configuration expected by ERP03.

This document intentionally contains names and requirements only; it contains no credentials or infrastructure secrets.
