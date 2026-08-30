# ERPNext Development Workspace Setup Guide

## Overview
This document provides complete setup instructions for the ERPNext v16.31.1 development environment based on the official Frappe Docker architecture.

## Extracted Configuration Data

### Target Versions
- **ERPNext**: v16.31.1
- **Frappe**: version-16 branch
- **Frappe Docker Reference**: v3.2.1
- **Container Registry**: ghcr.io/nyeinpyaesone-ui/erp03-erpnext

### Application Sources
```json
{
  "url": "https://github.com/frappe/erpnext",
  "branch": "version-16"
}
```

### Required Environment Variables
```bash
ERPNEXT_VERSION=v16.31.1
FRAPPE_BRANCH=version-16
FRAPPE_PATH=https://github.com/frappe/frappe
CUSTOM_IMAGE=ghcr.io/nyeinpyaesone-ui/erp03-erpnext
CUSTOM_TAG=<commit-sha-or-version>
PULL_POLICY=always
SITE_NAME=erp.example.com
SITES_RULE=Host(`erp.example.com`)
LETSENCRYPT_EMAIL=admin@example.com
DB_PASSWORD=<secret>
REDIS_CACHE=redis-cache:6379
REDIS_QUEUE=redis-queue:6379
GUNICORN_WORKERS=2
GUNICORN_THREADS=4
GUNICORN_TIMEOUT=120
MIGRATE_SITES=true
```

## Prerequisites

### System Requirements
- Docker 20.10+ with BuildKit support
- Docker Compose 1.29+ or Docker Compose V2
- Git
- Python 3.10+ (for local tooling)
- Minimum 8GB RAM, 4 CPU cores recommended
- 50GB+ free disk space

### Required Tools Installation

#### Ubuntu/Debian
```bash
# Update package index
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose (if not included with Docker)
sudo apt-get install docker-compose-plugin

# Install Git and Python
sudo apt-get install git python3 python3-pip python3-venv

# Verify installations
docker --version
docker compose version
git --version
python3 --version
```

#### macOS
```bash
# Install Docker Desktop (includes Docker Compose)
brew install --cask docker

# Install Git and Python
brew install git python3

# Verify installations
docker --version
docker compose version
git --version
python3 --version
```

#### Windows (WSL2)
```bash
# Install Docker Desktop for Windows with WSL2 backend
# Download from: https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe

# Install WSL2 and Ubuntu
wsl --install -d Ubuntu

# Inside WSL terminal, follow Ubuntu/Debian instructions above
```

## Development Environment Setup

### Step 1: Clone Required Repositories

```bash
cd /workspace/erpnext-dev

# Clone official Frappe Docker repository at pinned version
git clone --depth 1 --branch v3.2.1 https://github.com/frappe/frappe_docker.git

# Clone ERPNext repository (reference)
git clone --depth 1 --branch version-16 https://github.com/frappe/erpnext.git erpnext-ref

# Create custom apps directory
mkdir -p apps
```

### Step 2: Prepare Custom Apps Configuration

Create `apps.json` in the frappe_docker context:

```bash
cat > frappe_docker/apps.json << 'EOF'
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-16"
  }
]
EOF
```

### Step 3: Create Development Environment File

```bash
cat > frappe_docker/.env << 'EOF'
# Development Configuration
ERPNEXT_VERSION=v16.31.1
FRAPPE_BRANCH=version-16
FRAPPE_PATH=https://github.com/frappe/frappe

# Site configuration
SITE_NAME=erp.localhost
SITES_RULE=Host(`erp.localhost`)

# Development secrets (change in production!)
DB_PASSWORD=development_password_123
ADMIN_PASSWORD=admin123
REDIS_CACHE=redis-cache:6379
REDIS_QUEUE=redis-queue:6379

# Runtime settings
GUNICORN_WORKERS=2
GUNICORN_THREADS=4
GUNICORN_TIMEOUT=120

# Migration
MIGRATE_SITES=true
EOF
```

### Step 4: Build Custom Image (Development)

```bash
cd frappe_docker

# Build with BuildKit secrets
DOCKER_BUILDKIT=1 docker build \
  --file images/layered/Containerfile \
  --tag erp03-erpnext:dev \
  --build-arg FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg FRAPPE_BRANCH=version-16 \
  --secret id=apps_json,src=apps.json \
  .
```

### Step 5: Start Development Services

```bash
# Using the production compose architecture
docker compose -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.noproxy.yaml \
  up -d
```

### Step 6: Create Site and Install ERPNext

```bash
# Wait for services to be ready
docker compose ps

# Create new site
docker compose exec backend bench new-site erp.localhost \
  --mariadb-root-password development_password_123 \
  --admin-password admin123 \
  --no-mariadb-socket

# Install ERPNext app
docker compose exec backend bench --site erp.localhost install-app erpnext

# Set site as current site
docker compose exec backend bench use erp.localhost
```

### Step 7: Access Development Instance

Add to `/etc/hosts`:
```bash
echo "127.0.0.1 erp.localhost" | sudo tee -a /etc/hosts
```

Access the application:
- **URL**: http://erp.localhost:8000
- **Username**: Administrator
- **Password**: admin123

## Kubernetes/GitOps Development Setup

### Prerequisites for K8s Development
- kubectl configured for your cluster
- ArgoCD installed
- External Secrets Operator installed
- Prometheus/Grafana stack (optional)

### Deploy to Kubernetes (Development)

```bash
cd /workspace/infra/erpnext/gitops

# Update kustomization with dev image tag
kustomize edit set image ghcr.io/nyeinpyaesone-ui/erp03-erpnext:dev

# Create namespace
kubectl create namespace erpnext-dev --dry-run=client -o yaml | kubectl apply -f -

# Apply secrets (create dummy secret for development)
kubectl create secret generic erpnext-secrets \
  --from-literal=DB_HOST=mariadb.erpnext-dev.svc \
  --from-literal=DB_PASSWORD=development_password_123 \
  --from-literal=REDIS_URL=redis://redis-cache.erpnext-dev.svc:6379 \
  --namespace erpnext-dev \
  --dry-run=client -o yaml | kubectl apply -f -

# Apply all manifests
kustomize build . | kubectl apply -f -

# Or use kubectl directly
kubectl apply -k .
```

### Monitor Deployment

```bash
# Watch deployment status
kubectl get pods -n erpnext-dev -w

# Check logs
kubectl logs -n erpnext-dev -l app=erpnext -f

# Port-forward for local access
kubectl port-forward svc/erpnext -n erpnext-dev 8000:8000
```

Access at: http://localhost:8000

## Verification Checklist

### Basic Functionality Tests
- [ ] Site loads over HTTP/HTTPS
- [ ] Administrator login succeeds
- [ ] Dashboard displays correctly
- [ ] Company creation works
- [ ] Fiscal year configuration works
- [ ] Customer creation and retrieval works
- [ ] Supplier creation and retrieval works
- [ ] Item master creation works
- [ ] Warehouse setup works
- [ ] Purchase order creation works
- [ ] Sales order creation works
- [ ] Stock transaction posts correctly
- [ ] Accounting entries are created
- [ ] Reports render without errors
- [ ] Background jobs execute
- [ ] File upload/download functions
- [ ] Email configuration works (if configured)

### Technical Verification
- [ ] All pods are Running (kubectl get pods)
- [ ] No crash loops in pod events
- [ ] Database migrations completed successfully
- [ ] Redis cache is operational
- [ ] Redis queue is processing jobs
- [ ] Health endpoints respond (/api/method/ping)
- [ ] Metrics endpoint accessible (if configured)
- [ ] Logs show no critical errors

## Troubleshooting

### Common Issues

#### Container fails to start
```bash
# Check container logs
docker compose logs backend
docker compose logs db
docker compose logs redis-cache
docker compose logs redis-queue
```

#### Database connection errors
```bash
# Verify DB credentials
docker compose exec backend env | grep DB

# Test database connectivity
docker compose exec backend mysql -h db -u root -p
```

#### Site creation fails
```bash
# Remove partial site and retry
docker compose exec backend bench drop-site erp.localhost
docker compose exec bench new-site erp.localhost ...
```

#### Permission issues
```bash
# Fix file permissions
docker compose exec backend chown -R frappe:frappe /home/frappe/frappe-bench/sites
```

### Reset Development Environment

```bash
# Stop all services
docker compose down -v

# Remove all volumes
docker volume rm $(docker volume ls -q | grep erpnext)

# Clean and rebuild
docker system prune -f
docker builder prune -f

# Rebuild image
docker compose build --no-cache
```

## Production Readiness Notes

Before moving to production:

1. **Replace all placeholder values**:
   - Change DB_PASSWORD to a strong secret
   - Update SITE_NAME to production domain
   - Configure proper TLS certificates
   - Set LETSENCRYPT_EMAIL to admin email

2. **Security hardening**:
   - Use External Secrets or Vault for credentials
   - Enable network policies
   - Configure resource limits
   - Implement backup strategy

3. **Monitoring setup**:
   - Configure Prometheus scraping
   - Set up alerting rules
   - Enable log aggregation

4. **Backup configuration**:
   - Schedule database backups
   - Backup site files
   - Test restore procedures

## Reference Files Location

Original source files in ERP03 repository:
- Configuration: `/workspace/infra/erpnext/`
- CI/CD Workflows: `/workspace/.github/workflows/erpnext-production.yml`
- GitOps Manifests: `/workspace/infra/erpnext/gitops/`
- Custom Apps: `/workspace/apps/erpnext_custom/`

## Next Steps

1. Complete custom application development in `/workspace/apps/erpnext_custom/`
2. Run full UAT testing per IMPLEMENTATION-TASKS.md checklist
3. Address all P0 items before client UAT
4. Complete P1 items for production certification
5. Implement P2 items for enterprise hardening

## Support Resources

- Official Frappe Docker: https://github.com/frappe/frappe_docker
- ERPNext Documentation: https://docs.erpnext.com
- Frappe Framework Docs: https://frappeframework.com/docs
- Community Forum: https://discuss.frappe.io
