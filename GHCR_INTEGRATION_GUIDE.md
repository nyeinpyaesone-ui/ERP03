# 🐳 GHCR Container Registry Integration Guide

## Overview

This document provides comprehensive instructions for building, publishing, and managing Docker container images to GitHub Container Registry (GHCR) for the ERP03 system.

---

## 📋 Prerequisites

### Required Permissions
- **Repository Access**: Write permissions to the repository
- **Package Permissions**: `packages: write` in workflow files
- **GitHub Token**: Automatic via `secrets.GITHUB_TOKEN`

### Local Development Setup

```bash
# Install Docker Desktop or Docker Engine
# Verify Docker installation
docker --version

# Install Docker Buildx (multi-platform builds)
docker buildx version

# Login to GHCR locally
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin
```

---

## 🏗️ Architecture

### Container Images

| Image | Path | Description | Platforms |
|-------|------|-------------|-----------|
| **Backend** | `ghcr.io/{owner}/{repo}/erp-backend` | FastAPI WebSocket & REST API | linux/amd64, linux/arm64 |
| **Frontend** | `ghcr.io/{owner}/{repo}/erp-frontend` | React web application | linux/amd64 |
| **Worker** | `ghcr.io/{owner}/{repo}/erp-worker` | Background task processor | linux/amd64, linux/arm64 |

### Tagging Strategy

```yaml
Tags automatically generated:
- Branch-based: main, develop
- PR-based: pr-{number}
- Semantic versions: v1.2.3, v1.2, v1
- SHA-based: {commit-sha}
- Latest: latest (only on main branch)
```

---

## 🚀 CI/CD Pipeline

### Workflow Triggers

The `docker-publish.yml` workflow runs on:

1. **Push to main/develop**: Build and push images
2. **Pull requests**: Build only (validation)
3. **Release published**: Create versioned tags
4. **Manual trigger**: Via GitHub Actions UI

### Pipeline Stages

```mermaid
graph TD
    A[Code Push] --> B{Event Type}
    B -->|PR| C[Build Only]
    B -->|Main/Develop| D[Build + Push]
    B -->|Release| E[Build + Push + Version Tags]
    
    C --> F[Load Test]
    D --> G[Security Scan]
    E --> G
    G --> H[Generate SBOM]
    H --> I[Deploy Staging]
    I --> J[Publish Summary]
```

### Security Scanning

Every image undergoes:

1. **Base Image Scan**: Trivy scans base Python/Node images
2. **Built Image Scan**: Full vulnerability assessment
3. **Dependency Check**: Python `safety` + npm `audit`
4. **SBOM Generation**: SPDX format for compliance

---

## 📦 Building Images Locally

### Backend Image

```bash
cd /workspace/ERP-BACKEND

# Build for local testing
docker build -t erp-backend:local .

# Build multi-platform (requires buildx)
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ghcr.io/your-org/erp-backend:latest \
  --push \
  .

# Run locally
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/erp03 \
  -e REDIS_URL=redis://localhost:6379 \
  -e SECRET_KEY=dev-secret-key \
  erp-backend:local
```

### Frontend Image

```bash
cd /workspace/frontend

# Build
docker build -t erp-frontend:local .

# Run
docker run -p 3000:80 \
  erp-frontend:local
```

### Worker Image

```bash
cd /workspace/docker

# Build
docker build -f Dockerfile.worker -t erp-worker:local .

# Run
docker run \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/erp03 \
  -e REDIS_URL=redis://localhost:6379 \
  erp-worker:local
```

---

## 🔐 Authentication

### GitHub Actions (Automatic)

No manual authentication required. The workflow uses:

```yaml
- name: Log in to Container Registry (GHCR)
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

### Manual Authentication

```bash
# Create Personal Access Token (PAT)
# Go to: GitHub Settings > Developer settings > Personal access tokens
# Scopes required: read:packages, write:packages, delete:packages

# Login
echo $YOUR_PAT | docker login ghcr.io -u $YOUR_USERNAME --password-stdin

# Verify
docker logout ghcr.io
```

### Kubernetes Pull Secrets

```bash
# Create secret for pulling private images
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=$GITHUB_USERNAME \
  --docker-password=$GITHUB_TOKEN \
  --docker-email=your@email.com \
  -n erp03-system

# Reference in deployment
spec:
  containers:
  - name: backend
    image: ghcr.io/your-org/erp-backend:v1.2.3
  imagePullSecrets:
  - name: ghcr-secret
```

---

## 🎯 Deployment Strategies

### Staging Deployment (Automated)

Triggered on merge to `main`:

```yaml
deploy-staging:
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  environment:
    name: staging
    url: https://staging.erp03.example.com
```

### Production Deployment (Manual Approval)

Configure GitHub Environment protection rules:

1. Go to: Repository Settings > Environments
2. Create `production` environment
3. Enable "Required reviewers"
4. Add deployment branch restrictions

Update workflow:

```yaml
deploy-production:
  needs: [build-backend, build-frontend, build-worker]
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  environment:
    name: production
    url: https://erp03.example.com
```

### Kubernetes Manifest Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: erp-backend
  namespace: erp03-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: erp-backend
  template:
    metadata:
      labels:
        app: erp-backend
        version: v1.2.3
    spec:
      imagePullSecrets:
      - name: ghcr-secret
      containers:
      - name: backend
        image: ghcr.io/your-org/erp-backend:v1.2.3
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## 📊 Monitoring & Observability

### Image Metrics

Monitor via GitHub Insights:

- Package downloads
- Storage usage
- Vulnerability alerts

### Prometheus Metrics (Application)

Backend exposes metrics at `/metrics`:

```python
# WebSocket connections active
websocket_connections_total

# Message throughput
websocket_messages_sent_total
websocket_messages_received_total

# Latency histograms
websocket_message_latency_seconds
websocket_connection_duration_seconds
```

### Logging

Structured JSON logs with correlation IDs:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "erp-backend",
  "image_tag": "v1.2.3",
  "correlation_id": "abc-123-def",
  "event": "websocket_connected",
  "client_id": "user-456",
  "channel": "notifications"
}
```

---

## 🔧 Troubleshooting

### Build Failures

#### Issue: Multi-platform build fails
```bash
# Solution: Ensure buildx is properly configured
docker buildx create --use --name multiarch
docker buildx inspect --bootstrap
```

#### Issue: Permission denied pushing to GHCR
```bash
# Verify token permissions
# Required scopes: read:packages, write:packages

# Re-login
docker logout ghcr.io
echo $PAT | docker login ghcr.io -u $USERNAME --password-stdin
```

### Runtime Issues

#### Issue: Image pull failures in Kubernetes
```bash
# Check secret exists
kubectl get secrets ghcr-secret -n erp03-system

# Verify imagePullSecrets in deployment
kubectl describe deployment erp-backend -n erp03-system

# Check pod events
kubectl get events -n erp03-system --sort-by='.lastTimestamp'
```

#### Issue: WebSocket connection failures after deploy
```bash
# Check ingress configuration for WebSocket support
# Required headers:
#   Upgrade: websocket
#   Connection: Upgrade

# Verify health endpoint
curl https://staging.erp03.example.com/api/v1/health

# Check logs
kubectl logs -l app=erp-backend -n erp03-system --tail=100
```

### Security Scan Failures

#### Issue: Critical vulnerabilities detected
```bash
# View detailed scan results
trivy image ghcr.io/your-org/erp-backend:v1.2.3

# Update base image version in Dockerfile
FROM python:3.11-slim  # Update to latest patch version

# Rebuild and rescan
docker build -t erp-backend:patched .
trivy image erp-backend:patched
```

---

## 📈 Performance Optimization

### Build Cache Optimization

```yaml
# In GitHub Actions workflow
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### Layer Caching Best Practices

```dockerfile
# Copy dependency files first (changes less frequently)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code last (changes frequently)
COPY . .
```

### Image Size Reduction

```dockerfile
# Multi-stage build example
FROM python:3.11-slim AS builder
# ... build steps ...

FROM python:3.11-slim AS production
# Copy only necessary artifacts
COPY --from=builder /app /app
# Remove unnecessary packages
RUN apt-get remove --purge -y gcc libpq-dev
```

---

## 🎓 Best Practices

### Versioning

✅ **DO:**
- Use semantic versioning (vMAJOR.MINOR.PATCH)
- Tag with commit SHA for traceability
- Keep `latest` tag only for main branch

❌ **DON'T:**
- Overwrite existing version tags
- Use `latest` in production deployments
- Skip version tags for releases

### Security

✅ **DO:**
- Scan images before and after builds
- Generate SBOMs for compliance
- Use minimal base images (slim, alpine)
- Run as non-root user

❌ **DON'T:**
- Hardcode secrets in Dockerfiles
- Include development dependencies in production
- Expose unnecessary ports

### Reliability

✅ **DO:**
- Implement health checks
- Set resource limits
- Configure proper probes (liveness/readiness)
- Use image digest pinning for critical deployments

❌ **DON'T:**
- Deploy without testing in staging
- Skip rollback procedures
- Ignore failed security scans

---

## 📚 Additional Resources

- [GitHub Container Registry Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Buildx Documentation](https://docs.docker.com/buildx/working-with-buildx/)
- [Trivy Security Scanner](https://aquasecurity.github.io/trivy/)
- [Open Container Initiative (OCI) Specifications](https://opencontainers.org/)
- [Kubernetes Image Pull Secrets](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/)

---

## 📞 Support

For issues related to GHCR integration:

1. Check workflow logs in GitHub Actions
2. Review Trivy scan results in Security tab
3. Consult this guide's troubleshooting section
4. Open an issue in the repository

**Last Updated**: $(date -u +"%Y-%m-%dT%H:%M:%SZ")  
**Document Version**: 1.0.0
