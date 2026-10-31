# ERP03 — Configuration & Credentials Setup Guide

This document consolidates all secrets, workflow permissions, branch protection, and environment configuration needed to activate the CI/CD pipeline.

## 1. Repository Secrets (GitHub UI)

**URL:** `https://github.com/nyeinpyaesone-ui/ERP03/settings/secrets/actions`

### Required Secrets

| Secret | How to Generate | Purpose |
|--------|----------------|---------|
| `DOCKERHUB_TOKEN` | Docker Hub → Account Settings → Security → New Access Token (write access) | Push container images to Docker Hub |
| `POSTGRES_PASSWORD` | Your chosen strong password | Database access for CI & compose |
| `SECRET_KEY` | `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` | Application signing / sessions |
| `DATABASE_URL` | `postgresql+asyncpg://erp03:<password>@postgres:5432/erp03` | Backend database connection |

### Optional Secrets (Advanced Pipeline)

| Secret | How to Generate | Purpose |
|--------|----------------|---------|
| `COSIGN_KEY` | `cosign generate-key-pair k8s://erp03/signing-key` | Image signing |
| `COSIGN_PUB_KEY` | Public key from above | Image verification |
| `SLACK_WEBHOOK_URL` | Slack → Incoming Webhooks | Secret rotation alerts |
| `SLACK_BOT_TOKEN` | Slack → OAuth & Permissions | Bot messages |
| `PYPI_TOKEN` | PyPI → Account Settings → API tokens | Package publishing |

### How to Add

1. Go to the URL above
2. Click **New repository secret**
3. Enter name and value, click **Add secret**
4. Repeat for all secrets

---

## 2. Workflow Permissions

**URL:** `https://github.com/nyeinpyaesone-ui/ERP03/settings/actions`

1. Scroll to **Workflow permissions**
2. Select **"Read and write permissions"**
3. Click **Save**

This enables the `DOCKERHUB_TOKEN` (Docker Hub access token) so the container workflow can push to Docker Hub without a separate PAT.

---

## 3. Branch Protection

**URL:** `https://github.com/nyeinpyaesone-ui/ERP03/settings/branches`

Click **Add branch protection rule**:

| Setting | Value |
|---------|-------|
| Branch name pattern | `main` |
| Require a pull request before merging | ✅ Enabled |
| Required approving reviews | 1 |
| Require review from Code Owners | ✅ Enabled |
| Require status checks before merging | ✅ Enabled |
| Required status checks | `CI / backend`, `CI / frontend`, `Quality / lint`, `Security / dependency-audit`, `Container / build-backend`, `Container / build-frontend` |
| Require branches to be up to date | ✅ Enabled |
| Do not allow bypassing the above settings | ✅ Enabled |

---

## 4. GitHub Environments

**URL:** `https://github.com/nyeinpyaesone-ui/ERP03/settings/environments`

| Environment | Reviewers | Wait Timer | Secrets to Add |
|-------------|-----------|------------|----------------|
| `development` | None | 0 | `POSTGRES_PASSWORD`, `SECRET_KEY`, `DATABASE_URL` |
| `staging` | 1 | 5 min | `POSTGRES_PASSWORD`, `SECRET_KEY`, `DATABASE_URL` |
| `production` | 2 | 10 min | `POSTGRES_PASSWORD`, `SECRET_KEY`, `DATABASE_URL` |

To add environment secrets: Click environment → **Add secret** → Enter name and value.

---

## 5. Local Environment File

```bash
cd /home/ubuntu/ERP03/ERP-BACKEND
cp .env.example .env
```

Edit `.env`:

```ini
ENVIRONMENT=development
SECRET_KEY=<from-step-1>
POSTGRES_DB=erp03
POSTGRES_USER=erp03
POSTGRES_PASSWORD=<from-step-1>
DATABASE_URL=postgresql+asyncpg://erp03:<password>@postgres:5432/erp03
DATABASE_PATH=./.local/erp03.sqlite3
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

DOCKERHUB_REGISTRY=docker.io
DOCKERHUB_USERNAME=<your-dockerhub-username>
DOCKERHUB_TOKEN=<DockerHub_PAT-value>
DOCKERHUB_IMAGE_BACKEND=docker.io/<your-dockerhub-username>/erp03-backend
DOCKERHUB_IMAGE_FRONTEND=docker.io/<your-dockerhub-username>/erp03-frontend
IMAGE_TAG=latest
```

**Never commit `.env`** — it is gitignored.

---

## 6. Trigger the Pipeline

```bash
cd /home/ubuntu/ERP03
git push origin main
```

Or tag a release:

```bash
git tag v1.0.0 && git push origin v1.0.0
```

This triggers the Container workflow which builds and pushes:
- `docker.io/powerrangeranikg/erp03-backend`
- `docker.io/powerrangeranikg/erp03-frontend`

---

## 7. Pull Images

```bash
echo $DOCKERHUB_TOKEN | docker login docker.io -u $DOCKERHUB_USERNAME --password-stdin
docker pull docker.io/powerrangeranikg/erp03-backend:latest
docker pull docker.io/powerrangeranikg/erp03-frontend:latest
```

---

## 8. Current Repository State

| Item | Status |
|------|--------|
| Working tree | Clean |
| Remote | `origin/main` at `cbe60362` |
| Lint (ruff) | 0 findings |
| Format | Clean |
| Tests | 48 passed, 1 skipped |
| Alembic migrations | Single head, applies cleanly |
| GitHub Actions workflows | 11 workflows, all valid YAML |
| Secrets configured | ❌ Pending (you must add) |
| Workflow permissions | ❌ Pending (you must enable) |
| Branch protection | ❌ Pending (you must configure) |

---

## 9. Quick Verification

```bash
# Check pipeline ran
gh run list --repo nyeinpyaesone-ui/ERP03 --limit 5

# Check images in Docker Hub
gh api repos/nyeinpyaesone-ui/ERP03/packages/container/erp03-backend/versions

# Pull and run
docker run -p 8000:8000 docker.io/powerrangeranikg/erp03-backend:latest
curl http://localhost:8000/api/v1/healthz
```

---

## 10. Important Notes

- **Never paste credentials in chat.** Configure them directly in the GitHub UI.
- **DOCKERHUB_TOKEN** is a Docker Hub access token with push access.
- **Workflow permissions** must be "Read and write" for `GITHUB_TOKEN` to push to Docker Hub.
- **Branch protection** requires Code Owners review — `CODEOWNERS` file is already in the repo.
- All workflows use only official GitHub Actions (`actions/*`, `docker/*`, `github/codeql-action*`).
