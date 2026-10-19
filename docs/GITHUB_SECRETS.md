# GitHub Repository Secrets Configuration — ERP03

Configure these in GitHub: **Settings → Secrets and variables → Actions**

## Required Repository Secrets

| Secret Name | Description | Required For |
|-------------|-------------|--------------|
| `GITHUB_TOKEN` | GitHub personal access token with `write:packages` scope (auto-provided by GitHub Actions as `${{ github.token }}`) | Container build & push to GHCR |
| `GHCR_PAT` | Personal Access Token with `write:packages` and `read:packages` scopes for GHCR authentication | Container push (alternative to GITHUB_TOKEN) |
| `DOCKERHUB_USERNAME` | Docker Hub username (if pushing to Docker Hub) | Optional Docker Hub push |
| `DOCKERHUB_TOKEN` | Docker Hub personal access token | Optional Docker Hub push |
| `POSTGRES_PASSWORD` | PostgreSQL database password | docker-compose / CI services |
| `SECRET_KEY` | Application secret key (min 32 chars in production) | Backend / docker-compose / production |
| `DATABASE_URL` | SQLAlchemy async database URL | Backend / CI tests |

## Container Registry — GitHub Container Registry (GHCR)

ERP03 publishes container images to GHCR:

- Backend: `ghcr.io/nyeinpyaesone-ui/erp03-backend`
- Frontend: `ghcr.io/nyeinpyaesone-ui/erp03-frontend`

### Authentication

GitHub Actions automatically provides `GITHUB_TOKEN` with `packages: write` permission when the workflow has `permissions: packages: write`. No additional PAT is required for GHCR pushes from Actions.

For local docker pushes to GHCR, create a PAT with `write:packages` and `read:packages` scopes:

```bash
# Log in to GHCR locally
echo $GHCR_PAT | docker login ghcr.io -u $GHCR_USERNAME --password-stdin

# Push an image
docker push ghcr.io/nyeinpyaesone-ui/erp03-backend:latest
```

### Required Permission Settings

In the repository, ensure:

1. **Settings → Actions → General → Workflow permissions** → "Read and write permissions" (enables `GITHUB_TOKEN` with `packages: write`)
2. **Settings → Actions → General → Fork pull request workflows** → as needed
3. **Package settings** → `erp03-backend` and `erp03-frontend` packages → Package visibility (public/private)

## Docker Compose Local Development

### Minimal profile (default — SQLite journal)

```bash
docker compose up -d
```

### Full profile (PostgreSQL)

```bash
POSTGRES_PASSWORD=your-secure-password \
SECRET_KEY=your-32-char-secret \
CORS_ORIGINS=https://your-domain.com \
docker compose --profile full up -d
```

### Environment variables for compose

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `erp03` | PostgreSQL database name |
| `POSTGRES_USER` | `erp03` | PostgreSQL username |
| `POSTGRES_PASSWORD` | *(required)* | PostgreSQL password |
| `SECRET_KEY` | *(required)* | App secret key |
| `DATABASE_URL` | `sqlite+aiosqlite:///data/erp03.sqlite3` | Backend DB URL |
| `CORS_ORIGINS` | *(required)* | Comma-separated allowed CORS origins |
| `DATABASE_PATH` | `/data/erp03.sqlite3` | SQLite journal path |
| `ENVIRONMENT` | `production` | App environment |
