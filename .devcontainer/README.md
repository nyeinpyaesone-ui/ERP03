# ERPNext Development Container Setup

## Overview

This DevContainer provides a complete ERPNext development environment with OIDC authentication support, pre-configured for VS Code and GitHub Codespaces.

## Quick Start

### Using VS Code

1. **Install Extensions**
   - Install [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension
   - Install recommended extensions from `.devcontainer/devcontainer.json`

2. **Configure Environment Variables**
   
   Create a `.env` file in your workspace root:
   ```bash
   # Required: Generate a secure secret key
   SECRET_KEY=$(openssl rand -hex 32)
   
   # Optional: Enable OIDC authentication
   OIDC_ENABLED=false
   
   # Optional: OIDC Configuration (if enabled)
   OIDC_PROVIDER=keycloak
   OIDC_CLIENT_ID=erpnext-dev
   OIDC_CLIENT_SECRET=your-client-secret
   OIDC_BASE_URL=https://auth.yourcompany.com
   OIDC_REDIRECT_URI=http://localhost:8000/api/method/frappe.integrations.oauth2_logins.custom/login
   ```

3. **Open in Container**
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Select "Dev Containers: Reopen in Container"
   - Wait for the container to build and start

4. **Start Development**
   ```bash
   # Verify ERPNext installation
   bench --version
   
   # Create new site (if needed)
   bench new-site dev.localhost
   
   # Install apps
   bench --site dev.localhost install-app erpnext
   
   # Start development server
   bench serve --port 8000
   ```

### Using GitHub Codespaces

1. Click "Code" → "Codespaces" → "Create codespace on main"
2. Configure repository secrets:
   - Go to Repository Settings → Secrets → Actions
   - Add `SECRET_KEY` with a generated value
3. The container will automatically build with your secrets

## Features

### Pre-installed Tools
- **ERPNext v15.120.0** - Base ERP system
- **Python 3.11** - Development runtime
- **Git** - Version control
- **Docker-in-Docker** - Container development
- **Bench** - Frappe/ERPNext CLI tool

### Development Tools
- `black` - Code formatting
- `flake8` - Linting
- `pylint` - Static analysis
- `pytest` - Testing framework
- `ipython` - Interactive Python shell
- `ipdb` - Python debugger
- `pre-commit` - Git hooks

### VS Code Extensions
- Python (Pylance, Black, Flake8)
- Docker
- YAML support
- GitHub Copilot
- GitHub Pull Requests

### Port Forwarding
- **8000** - ERPNext web interface
- **9000** - Bench process manager

## OIDC Authentication Setup

### Development Mode

The DevContainer includes OIDC libraries (`authlib`, `requests-oauthlib`) pre-installed. To test OIDC locally:

1. Set environment variables in `.env`:
   ```bash
   OIDC_ENABLED=true
   OIDC_PROVIDER=keycloak
   OIDC_CLIENT_ID=erpnext-dev
   OIDC_CLIENT_SECRET=dev-secret
   OIDC_BASE_URL=http://localhost:8080
   ```

2. Run the configuration script:
   ```bash
   python3 /usr/local/bin/configure-oidc.py
   ```

3. Restart the bench server

### Production Mode

When deploying to production, use the CI/CD pipeline which automatically:
- Builds the DevContainer image
- Pushes to GHCR: `ghcr.io/<owner>/erpnext-devcontainer:latest`
- Configures secrets from GitHub Actions

## Customization

### Adding More Tools

Edit `.devcontainer/Dockerfile`:
```dockerfile
RUN pip3 install --no-cache-dir \
    your-package-here
```

### Changing Python Version

Update `.devcontainer/devcontainer.json`:
```json
"features": {
  "ghcr.io/devcontainers/features/python:1": {
    "version": "3.10"  // Change version here
  }
}
```

### Mounting Additional Volumes

Add to `mounts` array in `devcontainer.json`:
```json
"mounts": [
  "source=${localEnv:HOME}/.ssh,target=/home/devuser/.ssh,type=bind",
  "source=my-data,target=/workspace/data,type=volume"
]
```

## Troubleshooting

### Container Won't Start

1. Check Docker is running: `docker ps`
2. Verify environment variables are set
3. Rebuild container: `Ctrl+Shift+P` → "Dev Containers: Rebuild Container"

### SECRET_KEY Issues

Generate a new key:
```bash
openssl rand -hex 32
```

Add to `.env` file or VS Code settings.

### OIDC Configuration Fails

1. Verify all required OIDC environment variables are set
2. Check OIDC provider is accessible from container
3. Review logs: `docker logs <container-id>`

### Performance Issues

1. Increase Docker memory allocation (VS Code → Settings → Docker)
2. Use volume mounts instead of copying large files
3. Exclude unnecessary folders in `.devcontainer/.gitignore`

## CI/CD Integration

The DevContainer image is automatically built and pushed to GHCR when you push to main:

```yaml
# .github/workflows/devcontainer-build.yml
# Automatically builds and pushes to:
# ghcr.io/<owner>/erpnext-devcontainer:latest
```

### Manual Build

```bash
cd /workspace
docker build -f .devcontainer/Dockerfile \
  --build-arg SECRET_KEY=your-secret \
  --build-arg OIDC_ENABLED=false \
  -t erpnext-devcontainer:latest .
```

## Security Best Practices

1. **Never commit `.env` files** - Already in `.gitignore`
2. **Use GitHub Secrets** for sensitive values in CI/CD
3. **Rotate SECRET_KEY** periodically
4. **Use HTTPS** for OIDC providers in production
5. **Enable OIDC only when needed** (default: disabled)

## Resources

- [ERPNext Documentation](https://docs.frappe.io/erpnext)
- [Frappe Framework Docs](https://frappeframework.com/docs)
- [Dev Containers Spec](https://containers.dev/)
- [GitHub Codespaces](https://docs.github.com/en/codespaces)

## Support

For issues related to:
- **ERPNext**: https://github.com/frappe/erpnext/issues
- **Frappe Framework**: https://github.com/frappe/frappe/issues
- **DevContainer**: Open issue in this repository
