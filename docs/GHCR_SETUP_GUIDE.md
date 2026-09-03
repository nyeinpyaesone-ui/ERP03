# ERP erp03 - GitHub Container Registry (GHCR) Setup Guide

This guide explains how to configure and use GitHub Container Registry (GHCR) for the ERP erp03 project.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [GitHub Personal Access Token Setup](#github-personal-access-token-setup)
3. [Local Development Setup](#local-development-setup)
4. [GitHub Actions CI/CD](#github-actions-cicd)
5. [Pulling Images](#pulling-images)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Docker installed (version 20.10+)
- Docker Buildx enabled
- GitHub account with access to the repository
- Git configured locally

---

## GitHub Personal Access Token Setup

### Step 1: Create a Personal Access Token (Classic)

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select the following scopes:
   - ✅ `read:packages` - Download packages
   - ✅ `write:packages` - Upload packages
   - ✅ `repo` - Full control of private repositories (if repo is private)
4. Generate token and **copy it immediately** (you won't see it again)

### Step 2: Store Token Securely

```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export GHCR_TOKEN="ghp_your_token_here"
```

---

## Local Development Setup

### Step 1: Login to GHCR

```bash
# Login with your GitHub username
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

### Step 2: Build and Push Images Locally

```bash
# Make the script executable
chmod +x scripts/build-push-ghcr.sh

# Run the build script
./scripts/build-push-ghcr.sh v1.0.0-dev
```

### Step 3: Verify Images

Visit: https://github.com/YOUR_USERNAME?tab=packages&repo_name=erp03

---

## GitHub Actions CI/CD

The workflow automatically:

1. **Pre-flight Validation**: Checks environment files and repository structure
2. **Build Backend**: Builds and pushes backend image to GHCR
3. **Build Frontend**: Builds and pushes frontend image to GHCR
4. **Security Scanning**: Runs Trivy vulnerability scanner
5. **Integration Tests**: Runs tests against the built images
6. **Deployment Summary**: Generates deployment report

### Trigger Events

- Push to `main` branch → builds `latest` tag
- Push to `develop` branch → builds `develop` tag
- Tag push (e.g., `v1.0.0`) → builds versioned tag
- Pull request → builds but doesn't push

### Required Repository Secrets

No additional secrets needed! The workflow uses:
- `secrets.GITHUB_TOKEN` - Automatically provided by GitHub Actions

### Optional: Configure Package Visibility

1. Go to your repository's "Packages" section
2. Select the package
3. Click "Package Settings"
4. Under "Danger Zone", change visibility to:
   - **Private** (default) - Only accessible within organization
   - **Public** - Anyone can pull (requires authentication to push)

---

## Pulling Images

### Authentication Required

Even for public packages, you need to authenticate:

```bash
# Login first
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Pull specific version
docker pull ghcr.io/YOUR_USERNAME/erp03-backend:v1.0.0
docker pull ghcr.io/YOUR_USERNAME/erp03-frontend:v1.0.0

# Pull latest
docker pull ghcr.io/YOUR_USERNAME/erp03-backend:latest
docker pull ghcr.io/YOUR_USERNAME/erp03-frontend:latest
```

### Using in Docker Compose

```yaml
services:
  api:
    image: ghcr.io/YOUR_USERNAME/erp03-backend:latest
    # ... configuration
  
  frontend:
    image: ghcr.io/YOUR_USERNAME/erp03-frontend:latest
    # ... configuration
```

---

## Troubleshooting

### Issue: "unauthorized: authentication required"

**Solution**: Login to GHCR
```bash
docker login ghcr.io -u YOUR_GITHUB_USERNAME
```

### Issue: "denied: Your token has not been granted the required scopes"

**Solution**: Regenerate token with correct scopes:
- `read:packages`
- `write:packages`
- `repo`

### Issue: Build fails with "buildx not found"

**Solution**: Install/enable Docker Buildx
```bash
docker buildx create --use
```

### Issue: Multi-platform build fails

**Solution**: Ensure QEMU emulation is installed (for ARM builds on x86):
```bash
docker run --rm --privileged tonistiigi/binfmt --install all
```

### Issue: Package not visible after push

**Solution**: 
1. Check if push actually succeeded in GitHub Actions logs
2. Verify package visibility settings
3. Wait a few minutes for GitHub to process

---

## Image Tags Convention

| Tag Pattern | Description | Example |
|------------|-------------|---------|
| `latest` | Latest stable from main branch | `latest` |
| `develop` | Latest from develop branch | `develop` |
| `vX.Y.Z` | Semantic version release | `v1.0.0` |
| `vX.Y` | Minor version release | `v1.0` |
| `dev-YYYYMMDDHHMMSS` | Development build | `dev-20240115143022` |

---

## Security Best Practices

1. **Never commit tokens** to version control
2. **Rotate tokens regularly** (every 90 days recommended)
3. **Use minimum required scopes** for tokens
4. **Enable vulnerability scanning** (Trivy is included in CI)
5. **Review SBOMs** generated for each build
6. **Keep base images updated** to patch security vulnerabilities

---

## Cost Considerations

GitHub Packages storage limits:
- **Free tier**: 500 MB storage, 1 GB bandwidth/month
- **Pro tier**: 2 GB storage, 2 GB bandwidth/month
- **Team/Enterprise**: 50 GB storage, 50 GB bandwidth/month

Excess usage: $0.25/GB storage, $0.50/GB bandwidth overage

**Tip**: Clean up old images periodically:
```bash
# Delete old development images
ghcr delete YOUR_USERNAME/erp03-backend --version dev-*
```

---

## Support

For issues or questions:
- Open an issue on GitHub
- Check GitHub Actions logs
- Review Docker build output carefully
