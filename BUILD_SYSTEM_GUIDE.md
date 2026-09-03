# ERP03 Production Build System Documentation

## Overview

This document provides comprehensive guidance for the ERP03 professional build system, featuring:
- **Automated retry mechanisms** with exponential backoff
- **Fallback registry support** (GHCR ↔ Docker Hub)
- **Rate limiting** to prevent API throttling
- **Comprehensive error handling** for real-world scenarios
- **Security scanning** integration
- **Multi-platform builds** (AMD64/ARM64)

## Table of Contents

1. [Quick Start](#quick-start)
2. [Makefile Commands](#makefile-commands)
3. [CI/CD Pipeline](#cicd-pipeline)
4. [Build Script](#build-script)
5. [Configuration](#configuration)
6. [Error Handling](#error-handling)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

```bash
# Required tools
Docker >= 20.10
Docker Buildx >= 0.8
Git
Make (optional, for Makefile usage)
```

### Initial Setup

```bash
# 1. Initialize secrets for development
make init-secrets

# 2. Validate environment
make validate-env

# 3. Run pre-flight checks
make preflight

# 4. Start development environment
make dev-up
```

### Build & Deploy

```bash
# Development build (single platform, local)
make build-dev

# Production build (multi-platform, push to registry)
make build-prod VERSION=v1.0.0

# Full deployment pipeline
make deploy VERSION=v1.0.0
```

---

## Makefile Commands

### Build Commands

| Command | Description | Platform | Output |
|---------|-------------|----------|--------|
| `make build` | Default build (dev) | AMD64 | Local |
| `make build-dev` | Development build | AMD64 | Local |
| `make build-prod` | Production build | AMD64+ARM64 | Registry |
| `make push` | Push images | Multi | Registry |
| `make deploy` | Full deployment | Multi | K8s/Compose |

**Examples:**

```bash
# Build with custom version
make build-prod VERSION=v2.1.0

# Enable fallback registry
make deploy FALLBACK_ENABLED=true VERSION=v1.0.0

# Custom platform
make build-prod PLATFORMS=linux/amd64
```

### Testing Commands

| Command | Description | Retry | Coverage |
|---------|-------------|-------|----------|
| `make test` | All tests | Yes | Yes |
| `make lint` | Code linting | No | No |
| `make integration-tests` | Integration suite | Yes (1 retry) | Yes |
| `make coverage` | Generate report | No | HTML |
| `make security-scan` | Trivy scan | No | SARIF |

**Examples:**

```bash
# Run all tests
make test

# Security scan only
make security-scan

# View coverage report
make coverage
# Open: ERP-BACKEND/htmlcov/index.html
```

### Development Commands

```bash
# Start all services
make dev-up

# Stop all services
make dev-down

# Restart environment
make dev-restart

# Check service health
make health-check
```

**Service Endpoints:**

| Service | URL | Port |
|---------|-----|------|
| Frontend | http://localhost:5173 | 5173 |
| API | http://localhost:8000 | 8000 |
| PostgreSQL | localhost | 5432 |
| Redis | localhost | 6379 |
| Flower | http://localhost:5555 | 5555 |

### Maintenance Commands

```bash
# Clean build artifacts
make clean

# Complete cleanup (including images)
make clean-all

# Initialize secrets
make init-secrets

# Rotate secrets
make rotate-secrets

# Database backup
make backup

# Restore from backup
make restore

# Generate docs
make docs
```

---

## CI/CD Pipeline

### Workflow Stages

```
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: Pre-flight Checks & Validation                    │
│  - Repository checkout                                      │
│  - Version determination                                    │
│  - Registry availability check                              │
│  - Environment validation                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Stage 2: Backend Image Build (with retry)                  │
│  - Multi-platform build (AMD64 + ARM64)                     │
│  - Push to registry                                         │
│  - Trivy security scan                                      │
│  - SARIF upload to GitHub Security                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Stage 3: Frontend Image Build (with retry)                 │
│  - Multi-platform build (AMD64 + ARM64)                     │
│  - Push to registry                                         │
│  - Trivy security scan                                      │
│  - SARIF upload to GitHub Security                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Stage 4: Integration Tests                                 │
│  - PostgreSQL service                                       │
│  - Redis service                                            │
│  - Backend unit tests                                       │
│  - Coverage reporting                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Stage 5: Fallback Trigger (on failure)                     │
│  - Detect primary registry failure                          │
│  - Activate Docker Hub fallback                             │
│  - Notification generation                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Stage 6: Deployment Summary                                │
│  - Status aggregation                                       │
│  - Deployment notification                                  │
│  - GitHub Step Summary                                      │
└─────────────────────────────────────────────────────────────┘
```

### Retry Configuration

```yaml
# GitHub Actions retry settings
max_attempts: 3
timeout_minutes: 30
retry_on: error

# Exponential backoff
Attempt 1: Immediate
Attempt 2: +5 seconds delay
Attempt 3: +10 seconds delay
```

### Fallback Mechanism

When primary registry (GHCR) fails:

1. **Detection**: Registry availability check in preflight stage
2. **Activation**: Automatic switch to Docker Hub
3. **Rebuild**: Images tagged with `-backup` suffix
4. **Notification**: GitHub Step Summary updated

```yaml
# Fallback image naming
Primary: ghcr.io/owner/erp03-backend:v1.0.0
Fallback: docker.io/owner/erp03-backup-backend:v1.0.0
```

---

## Build Script

### Usage

```bash
# Basic usage
./scripts/build-push-ghcr.sh

# With custom version
./scripts/build-push-ghcr.sh v1.2.3

# Enable fallback
FALLBACK_ENABLED=true ./scripts/build-push-ghcr.sh

# Full options
VERSION=v1.0.0 \
FALLBACK_ENABLED=true \
MAX_RETRIES=5 \
./scripts/build-push-ghcr.sh
```

### Features

#### 1. Pre-flight Checks

- Docker installation verification
- Buildx availability check
- Registry login status (with retry)
- Directory structure validation
- Disk space check (minimum 10GB)

#### 2. Retry Logic

```bash
# Configuration
MAX_RETRIES=3
RETRY_DELAY=5  # Base delay in seconds

# Exponential backoff formula
delay = RETRY_DELAY × attempt_number

# Example:
# Attempt 1: 0s delay
# Attempt 2: 5s delay
# Attempt 3: 10s delay
```

#### 3. Rate Limiting

```bash
RATE_LIMIT_DELAY=2  # Seconds between API calls

# Applied before:
# - Registry login attempts
# - Build operations
# - Security scans
```

#### 4. Fallback Procedure

```bash
# Primary registry failure
if GHCR unavailable or build fails after MAX_RETRIES:
    if FALLBACK_ENABLED == true:
        Switch to Docker Hub
        Rebuild single-platform (AMD64)
        Tag with -fallback suffix
    else:
        Exit with error
```

#### 5. Security Scanning

```bash
# Trivy integration
trivy image --severity CRITICAL,HIGH \
    ghcr.io/owner/erp03-backend:v1.0.0

# Exit codes:
# 0: Scan completed (vulnerabilities logged)
# 1: Critical vulnerabilities found (if --exit-code 1)
```

### Output Logs

```bash
# Build logs location
/tmp/backend-build-<VERSION>.log
/tmp/frontend-build-<VERSION>.log

# Security scan logs
/tmp/trivy-backend-<VERSION>.log
/tmp/trivy-frontend-<VERSION>.log
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VERSION` | Git tag/timestamp | Image version tag |
| `REGISTRY_PRIMARY` | ghcr.io | Primary registry |
| `REGISTRY_FALLBACK` | docker.io | Backup registry |
| `IMAGE_PREFIX` | owner/erp03 | Image name prefix |
| `MAX_RETRIES` | 3 | Maximum retry attempts |
| `RETRY_DELAY` | 5 | Base delay (seconds) |
| `FALLBACK_ENABLED` | false | Enable fallback registry |
| `PLATFORMS` | amd64,arm64 | Build platforms |

### GitHub Secrets Required

```bash
# Required for CI/CD
GITHUB_TOKEN          # Auto-provided by GitHub
DOCKER_HUB_USERNAME   # Docker Hub username
DOCKER_HUB_TOKEN      # Docker Hub access token

# Optional
DEPLOY_KEY            # Kubernetes deployment key
SLACK_WEBHOOK         # Notification webhook
```

### Docker Compose Configuration

```yaml
# Resource limits (production)
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 1G

# Health checks
  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
```

---

## Error Handling

### Common Errors & Solutions

#### 1. Registry Authentication Failed

**Error:**
```
[ERROR] Failed to login to GHCR after 3 attempts
```

**Solutions:**
```bash
# Manual login
docker login ghcr.io -u <username>

# Verify token
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin

# Check token permissions
# Required: read:packages, write:packages, delete:packages
```

#### 2. Build Out of Memory

**Error:**
```
[ERROR] Build failed: out of memory
```

**Solutions:**
```bash
# Increase Docker memory
# Desktop: Settings → Resources → Memory (min 4GB)
# Server: Edit /etc/docker/daemon.json
{
  "default-shm-size": "2g"
}

# Single-platform build
make build-prod PLATFORMS=linux/amd64
```

#### 3. Low Disk Space

**Warning:**
```
[WARN] Low disk space detected: 5GB available (recommended: 10GB+)
```

**Solutions:**
```bash
# Clean Docker
docker system prune -a -f
docker buildx prune -f

# Makefile cleanup
make clean-all
```

#### 4. Security Scan Failures

**Warning:**
```
[WARN] Backend scan completed with warnings
```

**Solutions:**
```bash
# View detailed report
cat /tmp/trivy-backend-v1.0.0.log

# Fix vulnerable dependencies
# Backend
cd ERP-BACKEND
pip audit
pip install --upgrade <package>

# Frontend
cd frontend
npm audit
npm audit fix
```

#### 5. Integration Test Failures

**Error:**
```
Tests failed, retrying once...
```

**Solutions:**
```bash
# Check service health
make health-check

# View logs
docker-compose -f docker-compose.dev.yml logs db
docker-compose -f docker-compose.dev.yml logs redis

# Restart services
make dev-restart

# Run tests manually
cd ERP-BACKEND
pytest tests/ -v --tb=long
```

---

## Troubleshooting

### Diagnostic Commands

```bash
# Check Docker status
docker info
docker buildx version

# Verify registry access
curl -I https://ghcr.io
curl -I https://hub.docker.com

# List images
docker images | grep erp03

# Check build cache
docker buildx du

# View builder status
docker buildx inspect
```

### Reset Procedures

```bash
# Complete reset
make clean-all
rm -rf secrets/
make init-secrets

# Reset buildx
docker buildx rm erp-builder-*
docker buildx create --use --name erp-builder

# Reset GitHub Actions cache
# Go to: Settings → Actions → Caches → Delete all
```

### Contact & Support

- **Documentation**: `/workspace/SETUP_SUMMARY.md`
- **Build Script Docs**: `/workspace/scripts/BUILD_SCRIPT_DOCUMENTATION.md`
- **Kubernetes Guide**: `/workspace/kubernetes/README-Kubernetes.md`
- **GitHub Issues**: https://github.com/owner/erp03/issues

---

## Best Practices

### 1. Version Management

```bash
# Use semantic versioning
make build-prod VERSION=v1.2.3

# Tag releases in git
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

### 2. Security

```bash
# Always run security scans before deploy
make deploy  # Includes security-scan

# Rotate secrets monthly
make rotate-secrets

# Never commit secrets
# Add to .gitignore:
secrets/*.txt
.env.production
```

### 3. Performance

```bash
# Use build cache
docker buildx build --cache-from type=gha --cache-to type=gha,mode=max

# Multi-stage builds (already configured in Dockerfiles)
# Reduces image size by 60-80%
```

### 4. Monitoring

```bash
# Enable health checks (configured in docker-compose.yml)
# Monitor Flower dashboard: http://localhost:5555
# Check Prometheus metrics: http://localhost:9090
```

---

*Last Updated: $(date)*
*Version: 1.0.0*
