# GitHub Secrets Setup for Docker Push

> ⚠️ **Security policy:** Never commit real credentials (passwords, API keys,
> tokens) to this repository. All secret values must be stored in
> GitHub Secrets / a secrets manager and rotated regularly.

## Required Secrets

Go to: `https://github.com/<your-org>/<your-repo>/settings/secrets/actions`

### 1. Add Repository Variables

| Name | Value |
|------|-------|
| DOCKER_USER | `<your-docker-hub-username>` |

### 2. Add Repository Secrets

| Name | Value |
|------|-------|
| DOCKER_PAT_BACKEND | `<your-backend-token - starts with dckr_pat_>` |
| DOCKER_PAT_FRONTEND | `<your-frontend-token - starts with dckr_pat_>` |

### 3. Credential Rotation Checklist

If any credential may have been exposed, rotate it immediately:

1. **Docker Hub PATs** – Revoke old tokens at *Docker Hub → Account Settings → Security*, create new ones, and update `DOCKER_PAT_BACKEND` / `DOCKER_PAT_FRONTEND` in GitHub Secrets.
2. **Database / Redis passwords** – Update in your secrets manager and in `infra/k8s/base/secrets.yaml` placeholders (never with literal values).
3. **JWT / encryption keys** – Regenerate (`openssl rand -hex 32`) and roll out via Kubernetes Secrets only.
4. Verify `.env`, `.env.production.local`, and any `*.key` / `*.pem` files are git-ignored (see `.gitignore`).

### 4. How to Add

1. Click "New repository secret"
2. Enter Name (e.g., DOCKER_PAT_BACKEND)
3. Enter Value (paste your token)
4. Click "Add secret"
5. Repeat for all secrets

## After Setup

Push a tag to trigger build:
```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions will automatically:
- Build backend image
- Build frontend image
- Push both to Docker Hub

## Verify

Check your Docker Hub:
- https://hub.docker.com/r/powerrangeranikg/erp-solution-backend
- https://hub.docker.com/r/powerrangeranikg/erp-solution-frontend
