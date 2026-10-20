# ERP03 Environment Configuration

## Quick Start

### 1. Copy the environment template

```bash
cd ERP-BACKEND
cp ERP-BACKEND/.env.example ERP-BACKEND/.env
```

### 2. Generate a secure SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 3. Edit `.env` with your values

```ini
ENVIRONMENT=development
SECRET_KEY=<your-generated-secret-key>
POSTGRES_DB=erp03
POSTGRES_USER=erp03
POSTGRES_PASSWORD=<your-secure-password>
DATABASE_URL=postgresql+asyncpg://erp03:<your-secure-password>@postgres:5432/erp03
DATABASE_PATH=./.local/erp03.sqlite3
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# GHCR (optional, for container publishing)
GHCR_REGISTRY=ghcr.io
GHCR_USERNAME=<your-github-username>
GHCR_TOKEN=<your-github-pat-with-write-packages>
GHCR_IMAGE_BACKEND=ghcr.io/<your-github-username>/erp03-backend
GHCR_IMAGE_FRONTEND=ghcr.io/<your-github-username>/erp03-frontend
IMAGE_TAG=latest
```

### 4. Bootstrap the project

```bash
cd /home/ubuntu/ERP03
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 5. Start with Docker Compose

Minimal (SQLite journal):

```bash
docker compose up -d
```

Full (PostgreSQL):

```bash
POSTGRES_PASSWORD=<secure-password> \
SECRET_KEY=<secret-key> \
CORS_ORIGINS=https://your-domain.com \
docker compose --profile full up -d
```

## Production Deployment Checklist

- [ ] `SECRET_KEY` is set to a 32+ character random value
- [ ] `CORS_ORIGINS` contains only HTTPS origins (no `http://localhost`)
- [ ] `DATABASE_URL` points to production PostgreSQL
- [ ] `ENVIRONMENT=production`
- [ ] GHCR images are built and tagged
- [ ] Branch protection rules are configured (see PROTOCOLS.md)
- [ ] Required status checks pass on `main`

## GitHub Actions Secrets

Add these in **Settings → Secrets and variables → Actions**:

| Secret | Value Source |
|--------|--------------|
| `GITHUB_TOKEN` | Auto-provided by GitHub Actions |
| `GHCR_PAT` | GitHub PAT with `write:packages`, `read:packages` |
| `POSTGRES_PASSWORD` | Your chosen PostgreSQL password |
| `SECRET_KEY` | Your generated secret key |
| `DATABASE_URL` | Production database URL |

## Verification

```bash
# Backend health
curl http://localhost:8000/api/v1/healthz

# Frontend
curl http://localhost:3000

# GHCR images
docker pull ghcr.io/nyeinpyaesone-ui/erp03-backend:latest
docker pull ghcr.io/nyeinpyaesone-ui/erp03-frontend:latest
```
