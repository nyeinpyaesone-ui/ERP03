# Docker Registry Setup Guide

This guide explains how to configure and use the ERP03 Docker registry for building and pushing container images.

## Prerequisites

1. GitHub account with access to the repository
2. Docker installed with Buildx support
3. Git credentials configured

## Container Registry

ERP03 uses **GitHub Container Registry (GHCR)** as the primary container registry.

### Image Names

- Backend: `ghcr.io/<owner>/erp03-backend`
- Frontend: `ghcr.io/<owner>/erp03-frontend`

### Authentication

To push images to GHCR, you need to authenticate:

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u <github-username> --password-stdin
```

Where `$GITHUB_TOKEN` is a personal access token with `write:packages` scope.

## Building Images

### Using Makefile (Recommended)

```bash
# Build and push to GHCR
make push

# Build with specific version tag
VERSION=v1.0.0 make push
```

### Manual Build

```bash
# Build backend image
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ghcr.io/<owner>/erp03-backend:latest \
  -f ERP-BACKEND/Dockerfile . \
  --push

# Build frontend image
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ghcr.io/<owner>/erp03-frontend:latest \
  -f frontend/Dockerfile . \
  --push
```

## CI/CD Integration

Images are automatically built and pushed on:

- Push to `main` branch
- Release published
- Manual workflow dispatch

### GitHub Actions Workflow

The workflow is defined in `.github/workflows/docker-image.yml`:

```yaml
on:
  push:
    branches: [main]
  release:
    types: [published]
```

### Required Secrets

Configure these secrets in your GitHub repository:

- `GITHUB_TOKEN` (automatically provided)
- Optional: Custom registry credentials if using alternative registry

## Image Tags

| Tag Type | Format | Example |
|----------|--------|---------|
| Latest | `latest` | `ghcr.io/owner/erp03-backend:latest` |
| Git SHA | `<commit-sha>` | `ghcr.io/owner/erp03-backend:a1b2c3d` |
| Version | `v<major>.<minor>.<patch>` | `ghcr.io/owner/erp03-backend:v1.0.0` |
| Branch | `<branch-name>` | `ghcr.io/owner/erp03-backend:develop` |

## Pulling Images

```bash
# Login required for private repositories
echo $GITHUB_TOKEN | docker login ghcr.io -u <github-username> --password-stdin

# Pull images
docker pull ghcr.io/<owner>/erp03-backend:latest
docker pull ghcr.io/<owner>/erp03-frontend:latest
```

## Kubernetes Deployment

Update your Kubernetes manifests to use the new images:

```yaml
spec:
  containers:
  - name: erp-backend
    image: ghcr.io/<owner>/erp03-backend:v1.0.0
    imagePullPolicy: IfNotPresent
  - name: erp-frontend
    image: ghcr.io/<owner>/erp03-frontend:v1.0.0
    imagePullPolicy: IfNotPresent
```

Create image pull secret:

```bash
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=<github-username> \
  --docker-password=$GITHUB_TOKEN \
  --docker-email=<email>
```

## Troubleshooting

### Permission Denied

Ensure your token has `write:packages` scope:

```bash
# Create token with correct permissions
gh auth token --scopes write:packages
```

### Buildx Not Available

Install Docker Buildx:

```bash
# For Docker Desktop
# Already included

# For Linux
docker-buildx-plugin
```

### Multi-architecture Build Fails

Ensure QEMU emulation is enabled:

```bash
docker run --privileged --rm tonistiigi/binfmt --install all
```

## Alternative Registries

To use a different registry (Docker Hub, ECR, etc.), update the Makefile:

```makefile
DOCKER_REGISTRY=docker.io
# or
DOCKER_REGISTRY=<account>.dkr.ecr.<region>.amazonaws.com
```

Then build with:

```bash
DOCKER_REGISTRY=docker.io make push
```

## Security Best Practices

1. **Never commit credentials** - Use environment variables or secrets management
2. **Scan images** - Use Trivy or similar tools in CI/CD
3. **Use immutable tags** - Prefer SHA or version tags over `latest` in production
4. **Enable provenance** - SBOM and attestation generation is enabled by default
5. **Rotate tokens regularly** - Regenerate GitHub tokens periodically

## References

- [GitHub Container Registry Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Buildx Documentation](https://docs.docker.com/buildx/working-with-buildx/)
- [Container Security Best Practices](https://docs.docker.com/engine/security/)
