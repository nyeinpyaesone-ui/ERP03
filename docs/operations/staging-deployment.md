# Staging Deployment Gate

## Published images

The backend and frontend are published to GHCR with both `linux/amd64` and `linux/arm64` targets. The staging workflow accepts only the immutable `sha-<40-character-commit-sha>` tag so the two services can be selected from the same source revision.

Staging requires the following GitHub Environment secrets:

- `STAGING_SSH_HOST`
- `STAGING_SSH_USER`
- `STAGING_SSH_PORT` (optional; defaults to 22)
- `STAGING_SSH_PRIVATE_KEY`
- `STAGING_SSH_KNOWN_HOSTS`
- `STAGING_GHCR_USERNAME`
- `STAGING_GHCR_READ_TOKEN` (read-only package access)

The `staging` GitHub Environment must be configured with required reviewers and deployment branch restrictions in repository settings. The workflow's use of `environment: staging` does not itself prove those settings exist.

## Deployment behavior

The workflow can run only from `main`. It validates the immutable image tag, checks that the staging checkout is clean, requires an existing backend/frontend release for rollback, fetches the matching source commit, and verifies that commit is reachable from `origin/main`.

It then pulls the backend and frontend images from GHCR, starts them without building on the staging host, and waits for both Docker health checks to report `healthy`. The backend check calls `/api/v1/readyz`, which includes a database/schema readiness check. The frontend check requests the Nginx-served application root.

If application deployment or health validation fails, the workflow restores the previous source revision and previous image references, then waits for the previous containers to become healthy.

## Rollback boundary

The automated rollback restores application code and container images. It does not reverse database migrations or restore database data. Schema changes must use a backward-compatible expand/contract sequence. Any migration that cannot safely coexist with the prior application version requires a separately approved database backup and recovery plan before staging execution.

No staging deployment is automatic; this workflow is manually dispatched and gated by the GitHub Environment.
