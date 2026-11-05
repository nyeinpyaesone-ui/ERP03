# Staging Deployment Gate

## Published images

The backend and frontend are published to GHCR with both `linux/amd64` and `linux/arm64` targets. Each publisher verifies the registry manifest platforms and records the image digest in its GitHub Actions job summary. The staging workflow accepts the source commit SHA plus the backend and frontend OCI digests, and checks each image's `org.opencontainers.image.revision` label against that source commit before deployment. Deploying by digest avoids relying on mutable tags.

To prepare a staging request, use the successful main-branch backend and frontend publishing workflow summaries for the same source commit, and copy their exact `sha256:...` digests. Do not use PR workflow runs: PR builds do not publish images.

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

It then pulls the backend and frontend by digest, runs the one-off migration service from the same backend image, starts the application services without building on the staging host, and waits for both Docker health checks to report `healthy`. The migration service is not an application dependency, so the image rollback path does not rerun migrations. The backend check calls `/api/v1/readyz`, which includes a database/schema readiness check. The frontend check requests the Nginx-served application root.

If application deployment or health validation fails, the workflow restores the previous backend and frontend image references while keeping the Compose deployment configuration in place, then waits for the previous containers to become healthy. It does not attempt a database migration rollback.

## Rollback boundary

The automated rollback restores application code and container images. It does not reverse database migrations or restore database data. Schema changes must use a backward-compatible expand/contract sequence. Any migration that cannot safely coexist with the prior application version requires a separately approved database backup and recovery plan before staging execution.

No staging deployment is automatic; this workflow is manually dispatched and gated by the GitHub Environment.
