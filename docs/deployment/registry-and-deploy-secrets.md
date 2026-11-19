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
- Staging and production deployment pull from GHCR with a separate
  read-only machine identity. Do not reuse the Docker Hub publishing token or
  a GHCR publishing credential for deployment.

## Repository Actions secrets

Configure these under **Settings → Secrets and variables → Actions → Repository secrets**:

| Name | Purpose | Minimum access |
| --- | --- | --- |
| `DOCKERHUB_USERNAME` | Docker Hub user or organization namespace | Namespace identifier; not a password |
| `DOCKERHUB_TOKEN` | Push backend/frontend mirror images | Dedicated Docker Hub Organization Access Token (OAT), restricted to Image Push on the two ERP03 repositories, when using an organization namespace. For a personal namespace, use a separate publishing account if possible; a Personal Access Token's repository permission applies across all repositories that account can access. |

Create the Docker Hub repositories `erp03-backend` and `erp03-frontend`
under the selected namespace before enabling the mirror. The workflow publishes
multi-platform `linux/amd64` and `linux/arm64` images and verifies the manifest
and keyless Cosign signature in each registry.

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
| `GHCR_READ_USERNAME` | Machine identity allowed to pull ERP03 packages |
| `GHCR_READ_TOKEN` | Read-only GHCR package token |

Configure this **environment variable**:

| Name | Purpose |
| --- | --- |
| `STAGING_DEPLOY_PATH` | Absolute path to the staging Compose checkout |

The staging workflow logs the remote host out of GHCR after pulling images so
the read token is not left in its Docker credential store.

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
| `GHCR_READ_USERNAME` | Machine identity allowed to pull ERP03 packages |
| `GHCR_READ_TOKEN` | Read-only GHCR package token |

The production host must have its server-managed runtime configuration at
`$DEPLOY_PATH/shared/.env`. This file must be provisioned out of band with
production-only values and must not be committed or uploaded by the workflow.
The workflow links that file into each immutable release directory.

Enable required reviewers and prevent self-approval on the production
Environment. Restrict deployment branches to protected release tags or the
approved release branch according to the repository release policy.

## GHCR token policy

For private packages, use a dedicated machine identity and a token with only
`read:packages`; grant that identity access to the two ERP03 packages.
Prefer package-level read access and avoid `write:packages`, `delete:packages`,
or broad repository administration. If the packages are public, anonymous
pulls are possible, but retaining a dedicated read-only deployment identity
provides consistent behavior if visibility changes.

GHCR publishing itself must continue to use the job's `GITHUB_TOKEN` and
`packages: write`. Do not store a personal GHCR write token in Actions secrets.

## Host key and SSH handling

Generate a dedicated SSH key pair for each environment. Install only the public
key on the matching host and restrict it to the deployment account and required
deployment directory. Obtain the host public key fingerprint through a trusted
administrative channel, verify it independently, then store the matching
`known_hosts` entry in the environment secret. Do not trust an unverified
`ssh-keyscan` result.

## Validation checklist

- [ ] Docker Hub repositories exist and the token can push only those images.
- [ ] Repository secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` are set.
- [ ] GHCR package Actions access permits the repo workflow to publish.
- [ ] Staging and production environments have separate SSH keys and host-key pins.
- [ ] Each environment's GHCR machine identity can pull both required packages but cannot publish or delete them.
- [ ] Production host has a protected `shared/.env` file with correct runtime values.
- [ ] Production Environment requires an independent approval and restricts deployment refs.
- [ ] A trusted push/tag workflow verifies both registry manifests and signatures before deployment.
- [ ] A staging deployment and restore/rollback exercise pass before production is authorized.

Secret values are configured through GitHub's protected Settings UI; this
repository document records names and required permissions only.
