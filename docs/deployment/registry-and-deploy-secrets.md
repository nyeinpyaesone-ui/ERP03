# Registry and deployment credential configuration

This document defines the credential names and minimum access required by the
ERP03 GitHub Actions workflows. It intentionally contains no credential values.

## Registry design

- **GHCR is the primary registry.** GitHub Actions publishing uses the
  workflow-scoped `GITHUB_TOKEN` with `packages: write`; do not add a long-lived
  GHCR write token to repository secrets.
- **Docker Hub is an optional mirror.** Backend and frontend publishing enable
  the mirror only when both `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` exist.
  If either is absent, GHCR publishing continues and Docker Hub is skipped.
- Development/devcontainer images remain GHCR-only.
- Staging and production deployment pull from GHCR with each workflow's
  short-lived `GITHUB_TOKEN`, limited to `packages: read`. No long-lived GHCR
  pull token is stored as an Actions secret.

## Existing Docker1 environment

The backend and frontend publishing jobs use the existing GitHub Environment
named `Docker1`; they do not create or depend on new repository-level
credentials. Configure or retain the existing values under
**Settings → Environments → Docker1**:

| Name | GitHub setting | Purpose |
| --- | --- | --- |
| `DOCKERHUB_USERNAME` | Environment secret or variable | Docker Hub user/organization namespace |
| `DOCKERHUB_TOKEN` | Environment secret | Push backend/frontend mirror images |

The workflow reads the username from the environment secret first and falls
back to an environment variable of the same name. The token must be an
environment secret, never a variable. The workflow uses only these existing
names; if the current Docker1 entries use different names, align the workflow
references to those actual names rather than creating duplicates.

The existing Docker Hub repositories `erp03-backend` and `erp03-frontend`
must exist under the namespace supplied by `DOCKERHUB_USERNAME`. The workflow
publishes multi-platform `linux/amd64` and `linux/arm64` images and verifies
the manifest and keyless Cosign signature in each registry. Prefer an
Organization Access Token limited to Image Push on these two repositories.
A personal access token's repository permission applies to all repositories
the account can access.

Docker Hub distinguishes Personal Access Tokens (PATs) from Organization
Access Tokens (OATs). A PAT's repository permission applies across every
repository the account can access; it cannot be restricted to just the two
ERP03 repositories. For an organization namespace, prefer an OAT with Image
Push granted only to `erp03-backend` and `erp03-frontend`. For a personal
namespace, prefer a dedicated publishing account rather than granting a
personal account-wide Repo Read & Write token to CI. No delete or repository
administration scope is required.

The Docker Hub token must be rotated if it has ever been pasted into chat,
committed, logged, or otherwise exposed. Never put the token in workflow YAML,
repository files, shell command arguments, or deployment variables.

## Staging environment

Create the GitHub Environment named `staging`. Configure its **environment
secrets**:

| Name | Purpose |
| --- | --- |
| `STAGING_SSH_PRIVATE_KEY` | Dedicated SSH deploy key for the staging host |
| `STAGING_SSH_KNOWN_HOSTS` | Pre-verified SSH host key entries (not output copied blindly from `ssh-keyscan`) |
| `STAGING_SSH_HOST` | Staging host DNS name or IP |
| `STAGING_SSH_USER` | Restricted deployment account |
| `STAGING_SSH_PORT` | SSH port; optional, defaults to 22 |

GHCR pulls use the workflow's short-lived `GITHUB_TOKEN` with `packages: read`;
no GHCR environment secret is required.

Configure this **environment variable**:

| Name | Purpose |
| --- | --- |
| `STAGING_DEPLOY_PATH` | Absolute path to the staging Compose checkout |

The staging workflow removes its temporary GHCR workflow-token credential
from the remote Docker credential store after the image pull.

## Production environment

Create the GitHub Environment named `production`. Configure its **environment
secrets**:

| Name | Purpose |
| --- | --- |
| `DEPLOY_SSH_PRIVATE_KEY` | Dedicated production SSH deploy key |
| `DEPLOY_SSH_KNOWN_HOSTS` | Independently verified production SSH host key entries |
| `DEPLOY_HOST` | Production host DNS name or IP |
| `DEPLOY_USER` | Restricted deployment account |
| `DEPLOY_PATH` | Absolute production release root |
| `DEPLOY_SSH_PORT` | Optional SSH port; defaults to 22 |

GHCR pulls use the workflow's short-lived `GITHUB_TOKEN` with `packages: read`;
no GHCR environment secret is required.

The production host must have its server-managed runtime configuration at
`$DEPLOY_PATH/shared/.env`. This file must be provisioned out of band with
production-only values and must not be committed or uploaded by the workflow.
The workflow links that file into each immutable release directory. It uses a
fixed Compose project name (`erp03`) so versioned release directories continue
to use the same persistent PostgreSQL and Redis volumes. It deploys backend
and frontend by verified OCI digest, checks image revision labels against the
release source SHA, and attempts application-image rollback if health checks
fail. Database migrations must therefore follow an expand/contract strategy:
a migration must remain compatible with the previous application version
until the new release has passed health checks.

Enable required reviewers and prevent self-approval on the production
Environment. Restrict deployment branches to protected release tags or the
approved release branch according to the repository release policy.

## GHCR workflow-token policy

The staging and production workflows request only `packages: read` and
authenticate the remote host with the job's short-lived `GITHUB_TOKEN`. The
token is passed through SSH standard input, not a command-line argument, and
the remote Docker credential is removed after the pull (including failure
paths). No persistent GHCR token is required in either GitHub Environment.

In each GHCR package's **Package settings → Manage Actions access**, grant the
`nyeinpyaesone-ui/ERP03` repository the minimum role required to pull. If a
package is already linked to this repository, verify the inherited permissions.
For publishing, the workflows use `GITHUB_TOKEN` with `packages: write`;
for deployment, they use `packages: read`. Do not store a personal GHCR
write token in Actions secrets.

## Host key and SSH handling

Generate a dedicated SSH key pair for each environment. Install only the public
key on the matching host and restrict it to the deployment account and required
deployment directory. Obtain the host public key fingerprint through a trusted
administrative channel, verify it independently, then store the matching
`known_hosts` entry in the environment secret. Do not trust an unverified
`ssh-keyscan` result.

## Validation checklist

- [ ] Docker Hub repositories exist and the token can push only those images.
- [ ] Existing `Docker1` environment exposes `DOCKERHUB_USERNAME` as a secret or variable and `DOCKERHUB_TOKEN` as a secret.
- [ ] GHCR package Actions access permits the repo workflow to publish.
- [ ] Staging and production environments have separate SSH keys and host-key pins.
- [ ] GHCR package settings grant the ERP03 repository Actions access to pull the backend and frontend packages.
- [ ] Staging and production workflows receive only `packages: read` for GHCR pulls.
- [ ] Production host has a protected `shared/.env` file with correct runtime values.
- [ ] Production Environment requires an independent approval and restricts deployment refs.
- [ ] A trusted push/tag workflow verifies both registry manifests and signatures before deployment.
- [ ] A staging deployment and restore/rollback exercise pass before production is authorized.

Secret values are configured through GitHub's protected Settings UI; this
repository document records names and required permissions only.
