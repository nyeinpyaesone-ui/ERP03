# GitHub Secrets Setup for Docker Push

## Required Secrets

Go to: https://github.com/nyeinpyaesone-ui/ERP/settings/secrets/actions

### 1. Add Repository Variables

| Name | Value |
|------|-------|
| DOCKER_USER | powerrangeranikg |

### 2. Add Repository Secrets

| Name | Value |
|------|-------|
| DOCKER_PAT_BACKEND | (Your backend token - starts with dckr_pat_) |
| DOCKER_PAT_FRONTEND | (Your frontend token - starts with dckr_pat_) |

### 3. How to Add

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
