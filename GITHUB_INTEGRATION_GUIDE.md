# ERP03 CI/CD and GitHub Integration Guide

## Overview

This document provides comprehensive documentation for the ERP03 automated CI/CD pipeline and GitHub integration system.

## Repository Structure

```
.github/
├── workflows/
│   ├── ci-cd.yml                    # Legacy CI/CD pipeline
│   ├── ci-cd-optimized.yml          # Optimized reusable workflow pipeline
│   ├── docker-publish.yml           # Legacy Docker build and publish
│   ├── websocket-performance.yml    # WebSocket performance testing
│   ├── reusable-tests.yml           # Reusable test workflow
│   └── reusable-docker-build.yml    # Reusable Docker build workflow
```

## Automated Workflows

### 1. Main CI/CD Pipeline (`ci-cd-optimized.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests targeting `main` or `develop`

**Jobs:**
| Job | Description | Runs On |
|-----|-------------|---------|
| `backend-tests` | Python unit tests with coverage | Ubuntu |
| `frontend-tests` | React/TypeScript tests and build | Ubuntu |
| `mobile-tests` | React Native tests | Ubuntu |
| `integration-tests` | API contract tests | Ubuntu |
| `security-scan` | CodeQL, Bandit, npm audit | Ubuntu |
| `build-backend` | Docker image (multi-arch) | Ubuntu |
| `build-frontend` | Docker image | Ubuntu |
| `build-worker` | Worker Docker image | Ubuntu |
| `deploy-staging` | Kubernetes deployment | Ubuntu |
| `quality-gate` | Final validation gate | Ubuntu |
| `publish-summary` | Build summary report | Ubuntu |

### 2. Reusable Workflows

#### `reusable-tests.yml`

Parameterized test workflow supporting:
- `test-type`: backend, frontend, mobile, integration
- `python-version`: Default 3.11
- `node-version`: Default 18
- `coverage-min`: Minimum coverage threshold (default 80%)

**Usage Example:**
```yaml
jobs:
  test:
    uses: ./.github/workflows/reusable-tests.yml
    with:
      test-type: backend
      python-version: '3.11'
      coverage-min: 80
```

#### `reusable-docker-build.yml`

Parameterized Docker build workflow supporting:
- `component`: backend, frontend, worker
- `context`: Build context path
- `dockerfile`: Dockerfile location
- `platforms`: Target platforms (default: linux/amd64)
- `push`: Push to registry (default: true)

**Features:**
- Multi-platform builds (AMD64 + ARM64)
- Trivy vulnerability scanning
- SBOM generation
- Docker layer caching via GitHub Actions Cache

### 3. Docker Publishing (`docker-publish.yml`)

**Registry:** GitHub Container Registry (GHCR)
**Images:**
- `ghcr.io/{owner}/erp-backend`
- `ghcr.io/{owner}/erp-frontend`
- `ghcr.io/{owner}/erp-worker`

**Tagging Strategy:**
| Event | Tag Format |
|-------|------------|
| Branch push | `{branch-name}` |
| Pull request | `pr-{number}` |
| Semantic version tag | `{version}`, `{major}.{minor}` |
| Main branch | `latest`, `{sha}` |

## Branch Protection Strategy

### Development Isolation

```
feature/* → PR → develop → PR → main → GHCR Deploy
```

**Branch Rules:**
- `main`: Protected, requires PR review, all checks must pass
- `develop`: Protected, requires PR review, tests must pass
- `feature/*`: Unprotected, local development only

**GHCR Push Conditions:**
- ✅ Push to `main`: Full deploy with staging
- ✅ Push to `develop`: Build and push images (no deploy)
- ❌ Pull requests: Build only (load, no push)
- ❌ Feature branches: No workflow triggered

## Security Features

### Vulnerability Scanning
1. **Trivy**: Container image scanning (CRITICAL/HIGH severity)
2. **CodeQL**: Static code analysis (Python + JavaScript)
3. **Bandit**: Python security linter
4. **npm audit**: JavaScript dependency vulnerabilities
5. **Safety**: Python dependency vulnerabilities

### SBOM Generation
- Format: SPDX JSON
- Retention: 90 days
- Uploaded as workflow artifacts

### Secret Management
- GitHub Secrets for credentials
- `.env*` files excluded from Git
- GITHUB_TOKEN auto-provisioned for GHCR access

## Environment Configuration

### Required GitHub Secrets

| Secret | Description | Required For |
|--------|-------------|--------------|
| `GITHUB_TOKEN` | Auto-generated | GHCR authentication |
| `CODECOV_TOKEN` | Codecov upload token | Coverage reports |
| `KUBE_CONFIG` | Kubernetes credentials | Production deploy |
| `DEPLOY_KEY` | SSH deploy key | Staging/Production |

### GitHub Environments

Configure in Repository Settings → Environments:

**Staging:**
- Name: `staging`
- URL: `https://staging.erp03.example.com`
- Deployment branches: `main` only

**Production:**
- Name: `production`
- URL: `https://erp03.example.com`
- Required reviewers: Enable
- Deployment branches: `main` only with manual approval

## Local Development Setup

### Prerequisites
```bash
# Install smee-client for webhook forwarding
npm install --global smee-client

# Start webhook forwarder
smee -u https://smee.io/YOUR_CHANNEL_ID
```

### Testing Workflows Locally

```bash
# Using act (GitHub Actions local runner)
brew install act

# Run full CI/CD pipeline
act -j quality-gate

# Run specific job
act -j backend-tests

# Run with verbose output
act -v
```

## Monitoring and Alerts

### Workflow Status Badges

Add to README.md:
```markdown
![CI/CD](https://github.com/{owner}/erp03/actions/workflows/ci-cd-optimized.yml/badge.svg)
![Docker Publish](https://github.com/{owner}/erp03/actions/workflows/docker-publish.yml/badge.svg)
```

### Notifications

Configure in GitHub Repository Settings → Notifications:
- Email notifications for failed workflows
- Slack integration via GitHub Actions
- Microsoft Teams webhooks

## Troubleshooting

### Common Issues

**1. Docker build fails on ARM64**
```yaml
# Ensure multi-platform support
platforms: linux/amd64,linux/arm64
```

**2. GHCR authentication error**
```yaml
# Verify login step
uses: docker/login-action@v3
with:
  registry: ghcr.io
  username: ${{ github.actor }}
  password: ${{ secrets.GITHUB_TOKEN }}
```

**3. Test timeout in CI**
```yaml
# Increase service health check retries
options: >-
  --health-cmd pg_isready
  --health-interval 10s
  --health-timeout 5s
  --health-retries 10  # Increase from 5
```

**4. Coverage upload fails**
```yaml
# Verify file path exists
uses: codecov/codecov-action@v3
with:
  file: ./erp-core/coverage.xml  # Check this path
```

### Debug Mode

Enable step debugging:
```yaml
- name: Debug step
  run: |
    echo "Environment: ${{ env.DATABASE_URL }}"
    ls -la
  shell: bash
```

Set `ACTIONS_STEP_DEBUG=true` secret for verbose logs.

## Performance Optimization

### Build Caching

```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

### Parallel Jobs

All test jobs run in parallel:
- backend-tests
- frontend-tests
- mobile-tests
- security-scan

### Conditional Execution

```yaml
# Only build worker on main branch
if: github.event_name != 'pull_request' && github.ref == 'refs/heads/main'
```

## Compliance and Audit

### Artifact Retention
- SBOM files: 90 days
- Test coverage: 30 days
- Build logs: 90 days (GitHub default)

### Access Control
- Write access required for workflow modifications
- Admin access for environment configuration
- Read access for viewing workflow runs

### Version Control
- All workflow changes require PR review
- Workflow history available in Actions tab
- Previous versions restorable via Git

## Next Steps

1. **Configure GitHub Environments** in repository settings
2. **Add Required Secrets** (CODECOV_TOKEN, KUBE_CONFIG)
3. **Enable Branch Protection** rules for main/develop
4. **Test Pipeline** with a feature branch PR
5. **Monitor First Run** and adjust timeouts/thresholds

## Support

For issues or questions:
- Review workflow logs in GitHub Actions tab
- Check repository Insights → Pulse for trends
- Contact DevOps team for environment access
