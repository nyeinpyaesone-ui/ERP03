# GitHub Repository Secrets Configuration — ERP03

Configure these in GitHub: **Settings → Secrets and variables → Actions**

## Required Repository Secrets

| Secret Name | Description | Required For |
|-------------|-------------|--------------|
| `DOCKERHUB_USERNAME` | Docker Hub username (e.g., `powerrangeranikg`) | Container build & push to Docker Hub |
| `DOCKERHUB_TOKEN` | Docker Hub personal access token | Container push to Docker Hub |
| `POSTGRES_PASSWORD` | PostgreSQL database password | docker-compose / CI services |
| `SECRET_KEY` | Application secret key (min 32 chars in production) | Backend / docker-compose / production |
| `DATABASE_URL` | SQLAlchemy async database URL | Backend / CI tests |

## Container Registry — Docker Hub

ERP03 publishes container images to Docker Hub:

- Backend: `powerrangeranikg/erp03-backend`
- Frontend: `powerrangeranikg/erp03-frontend`

### Authentication

Docker Hub credentials must be configured as repository secrets:
- `DOCKERHUB_USERNAME` — your Docker Hub username
- `DOCKERHUB_TOKEN` — Docker Hub access token (not password)

For local docker pushes to Docker Hub:

```bash
# Log in to Docker Hub locally
echo $DOCKERHUB_TOKEN | docker login docker.io -u $DOCKERHUB_USERNAME --password-stdin

# Push an image
docker push powerrangeranikg/erp03-backend:latest
```

### Required Permission Settings

In the repository, ensure:

1. **Settings → Actions → General → Workflow permissions** → "Read and write permissions" (enables `${{ github.token }}` for any workflow needs)
2. **Settings → Actions → General → Fork pull request workflows** → as needed

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
