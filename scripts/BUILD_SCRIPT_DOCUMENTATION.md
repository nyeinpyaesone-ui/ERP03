# ERP erpo3 — Enhanced Build & Push Script Documentation

## Overview

The `build-push-ghcr.sh` script has been professionally refactored with enterprise-grade features for reliable, production-ready container image builds and deployments to GitHub Container Registry (GHCR).

## Key Features

### 🔄 Automated Retry Logic
- **Configurable retry attempts** (default: 3 retries)
- **Exponential backoff** between retry attempts
- **Automatic cleanup** of failed build artifacts before retry
- Applied to all critical operations:
  - Docker registry login
  - Buildx builder creation
  - Image build and push
  - Security scanning

### 🛡️ Fallback Mechanism
- **Primary registry**: GHCR (ghcr.io)
- **Fallback registry**: Docker Hub (docker.io) - configurable
- **Automatic failover** when primary registry is unavailable
- **Single-platform fallback** when multi-platform builds fail
- Clear indicators in output when fallback mode is active

### ⏱️ Rate Limiting
- **Built-in rate limit compliance** (default: 2 seconds between API calls)
- **Prevents registry throttling** during high-frequency operations
- **Respects GitHub API limits** for CI/CD pipelines

### 🔍 Enhanced Error Handling
- **Comprehensive logging** with timestamps
- **Build artifact preservation** for debugging
- **Graceful degradation** on non-critical failures
- **Exit code management** for CI/CD integration

### 🧹 Resource Management
- **Disk space validation** (minimum 10GB recommended)
- **Automatic cleanup** of temporary buildx builders
- **Optional dangling image removal** (configurable)
- **Build log preservation** in `/tmp/` directory

### 🔒 Security Features
- **Trivy vulnerability scanning** (when installed)
- **Retry logic for security scans**
- **Scan result logging** for compliance
- **Non-blocking scan failures** (warnings only)

## Configuration Variables

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_REPOSITORY_OWNER` | `$(whoami)` | GitHub organization or username |
| `VERSION` | `dev-YYYYMMDDHHMMSS` | Image version tag |
| `FALLBACK_ENABLED` | `false` | Enable fallback to Docker Hub |
| `MAX_RETRIES` | `3` | Maximum retry attempts per operation |
| `RETRY_DELAY` | `5` | Delay between retries (seconds) |
| `RATE_LIMIT_DELAY` | `2` | Rate limiting delay (seconds) |
| `CLEANUP_DANGLING_IMAGES` | `false` | Remove dangling images after build |

### Usage Examples

```bash
# Basic usage (development build)
./scripts/build-push-ghcr.sh

# Specific version tag
./scripts/build-push-ghcr.sh v1.2.3

# With fallback enabled
FALLBACK_ENABLED=true ./scripts/build-push-ghcr.sh

# Custom retry configuration
MAX_RETRIES=5 RETRY_DELAY=10 ./scripts/build-push-ghcr.sh v2.0.0

# Full production build with cleanup
FALLBACK_ENABLED=true CLEANUP_DANGLING_IMAGES=true ./scripts/build-push-ghcr.sh prod-2024.01.15
```

## Script Architecture

### Main Functions

1. **`preflight_checks()`**
   - Validates Docker installation
   - Checks Buildx availability
   - Authenticates with registry (with retry)
   - Validates directory structure
   - Checks available disk space
   - Activates fallback registry if needed

2. **`build_backend()`**
   - Creates isolated buildx builder instance
   - Builds multi-platform images (amd64/arm64)
   - Implements retry with artifact cleanup
   - Falls back to single-platform on failure
   - Preserves build logs

3. **`build_frontend()`**
   - Similar to backend build with frontend-specific configurations
   - Includes Vite build arguments
   - Maintains separate log files

4. **`run_security_scan()`**
   - Scans both backend and frontend images
   - Uses Trivy for vulnerability detection
   - Implements retry logic
   - Non-blocking on scan failures

5. **`generate_summary()`**
   - Displays build configuration
   - Shows pushed image locations
   - Provides pull commands
   - Indicates fallback mode if active
   - Lists log file locations
   - Cleans up temporary builders

6. **`cleanup_on_exit()`**
   - Removes temporary buildx builders
   - Optionally removes dangling images
   - Ensures clean state for next build

## Error Recovery

### Common Issues and Solutions

#### 1. Registry Authentication Failure
```
[WARNING] Not logged in to GHCR (Attempt 1/3)
[INFO] Attempting GHCR login... (Attempt 1/3)
```
**Solution**: Ensure you have a valid GitHub Personal Access Token with `write:packages` scope.

#### 2. Multi-Platform Build Failure
```
[WARNING] Backend build failed (Attempt 3/3)
[WARNING] Attempting fallback: single-platform (amd64) build...
```
**Solution**: Script automatically falls back to amd64-only build. Check QEMU emulation setup for arm64 support.

#### 3. Low Disk Space
```
[WARNING] Low disk space detected: 8GB available (recommended: 10GB+)
```
**Solution**: Free up disk space or enable `CLEANUP_DANGLING_IMAGES=true`.

#### 4. Trivy Scan Timeout
```
[WARNING] Backend scan encountered issues (Attempt 2/3)
```
**Solution**: Scan continues with retry. Install latest Trivy version for best performance.

## Build Logs

All build operations generate detailed logs:

- **Backend Build**: `/tmp/backend-build-{VERSION}.log`
- **Frontend Build**: `/tmp/frontend-build-{VERSION}.log`
- **Backend Security**: `/tmp/trivy-backend-{VERSION}.log`
- **Frontend Security**: `/tmp/trivy-frontend-{VERSION}.log`

## CI/CD Integration

### GitHub Actions Example

```yaml
jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and Push
        run: |
          chmod +x ./scripts/build-push-ghcr.sh
          FALLBACK_ENABLED=true ./scripts/build-push-ghcr.sh ${{ github.sha }}
```

### GitLab CI Example

```yaml
build:
  stage: build
  variables:
    FALLBACK_ENABLED: "true"
    MAX_RETRIES: "5"
  script:
    - chmod +x ./scripts/build-push-ghcr.sh
    - ./scripts/build-push-ghcr.sh ${CI_COMMIT_SHORT_SHA}
```

## Best Practices

1. **Always use specific version tags** for production builds
2. **Enable fallback mode** in CI/CD pipelines for reliability
3. **Monitor disk space** before large builds
4. **Review security scan logs** before deploying to production
5. **Clean up old images** from registry periodically
6. **Use environment variables** for sensitive configuration
7. **Test fallback registry** access periodically

## Troubleshooting

### Enable Verbose Logging
```bash
set -x
./scripts/build-push-ghcr.sh
```

### Test Registry Access
```bash
docker login ghcr.io
docker pull ghcr.io/your-org/erpo3-backend:latest
```

### Manual Builder Cleanup
```bash
docker buildx ls
docker buildx rm erp-builder-*
```

### Check Build Cache
```bash
docker buildx du
docker buildx prune
```

## Performance Optimization

### Parallel Builds
For independent services, consider parallel builds:
```bash
./scripts/build-push-ghcr.sh backend &
./scripts/build-push-ghcr.sh frontend &
wait
```

### Cache Optimization
- Use `--cache-from type=gha` in GitHub Actions
- Maintain consistent build environments
- Avoid unnecessary base image updates

### Multi-Architecture Considerations
- amd64 builds are faster than arm64 emulation
- Consider separate pipelines for different architectures
- Use native ARM runners for arm64 builds

## Support

For issues or questions:
1. Check build logs in `/tmp/`
2. Review this documentation
3. Verify environment configuration
4. Test with fallback mode enabled
5. Contact DevOps team

---

**Version**: 2.0.0  
**Last Updated**: 2024  
**Maintainer**: ERP erpo3 DevOps Team
