# GitHub Actions secrets and environments — ERP03

Configure deployment credentials in **Settings → Environments**. Keep staging and production credentials separate. Do not store runtime application secrets in source control.

## Container publishing

The active image workflows publish to GitHub Container Registry (GHCR):

- `ghcr.io/nyeinpyaesone-ui/erp03-backend`
- `ghcr.io/nyeinpyaesone-ui/erp03-frontend`

GitHub Actions authenticates with its automatically provided `GITHUB_TOKEN` and explicit `packages: write` permission. **No Docker Hub username or PAT is required.** Pull requests build images without logging into GHCR or publishing packages. Main/tag workflows publish immutable digests and attach provenance/SBOM; backend images are signed with cosign.

## Staging environment

The `deploy-staging.yml` workflow requires the following secrets in the GitHub `staging` environment:

| Name | Purpose |
|---|---|
| `STAGING_SSH_PRIVATE_KEY` | Restricted SSH deployment key |
| `STAGING_SSH_KNOWN_HOSTS` | Pinned staging host key(s) |
| `STAGING_SSH_HOST` | Staging server hostname |
| `STAGING_SSH_USER` | Restricted deployment account |
| `STAGING_SSH_PORT` | SSH port; optional, defaults to 22 |
| `STAGING_GHCR_USERNAME` | GHCR account/user for remote pulls |
| `STAGING_GHCR_READ_TOKEN` | Read-only GHCR token with `read:packages` |

Configure `STAGING_DEPLOY_PATH` as an environment variable (not a secret). The workflow is manually dispatched from `main`, validates source SHA and OCI digests, deploys those exact digests, verifies backend/frontend health, and restores the previous images on failure.

## Production environment

The `production-deploy.yml` workflow requires these secrets in the GitHub `production` environment:

| Name | Purpose |
|---|---|
| `DEPLOY_SSH_PRIVATE_KEY` | Restricted production SSH deployment key |
| `DEPLOY_HOST` | Production server hostname |
| `DEPLOY_USER` | Restricted deployment account |
| `DEPLOY_PATH` | Release directory on the host |
| `GHCR_USERNAME` | GHCR account/user for remote pulls |
| `GHCR_TOKEN` | Read-only GHCR token with `read:packages` |

Production deployment is a separate manually dispatched workflow and requires the explicit `DEPLOY-PRODUCTION` confirmation input plus environment protection approval.

## Release publishing

- `PYPI_TOKEN`: PyPI publishing token used only by the release workflow.

## Runtime application secrets

Keep `SECRET_KEY`, database credentials, Redis credentials, `DATABASE_URL`, and (when enabling the optional Supabase bridge) `SUPABASE_URL` plus `SUPABASE_PUBLISHABLE_KEY` in the target environment's secret manager or protected host-side environment file. The publishable key is intended for browser use; the backend uses it only to call Supabase Auth's user-verification endpoint. Never provide `SUPABASE_SECRET_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, or `SUPABASE_JWT_SECRET` to the frontend. They are not GHCR credentials and should not be copied into GitHub workflow variables unless a workflow explicitly requires them.

## Rotation

Any token or private key pasted into chat, logs, or a repository must be considered exposed and rotated. Use least-privilege, environment-scoped credentials; never reuse a personal account token for deployment automation.
