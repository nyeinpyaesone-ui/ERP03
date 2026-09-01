# ERPNext Production Deployment

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![ERPNext v15](https://img.shields.io/badge/ERPNext-v15.120.0-blue.svg)](https://erpnext.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-green.svg)](https://www.docker.com/)

## Overview

Production-ready ERPNext deployment with OIDC authentication support and automated GHCR image publishing. This repository provides a streamlined, containerized ERPNext setup optimized for enterprise deployments.

### Key Features

- **🔐 OIDC Authentication**: Optional SSO support (Keycloak, Google, Auth0, Azure AD, Okta)
- **🐳 Docker-Native**: Optimized builds with layer caching
- **🚀 CI/CD Pipeline**: Automated build, push, and setup via GitHub Actions
- **📦 GHCR Registry**: Images published to `ghcr.io/<owner>/erpnext` and `ghcr.io/<owner>/erpnext-nginx`
- **🛡️ Security**: Non-root containers, pinned actions, secret management
- **⚙️ Configuration**: Flexible environment-based configuration

---

## Quick Start

### Prerequisites

- Docker & Docker Compose v2+
- Git
- Access to GitHub Container Registry (GHCR)

### 1. Clone Repository

```bash
git clone https://github.com/<owner>/ERP03.git
cd ERP03
```

### 2. Configure Environment

```bash
cp .env.production.example .env
```

Edit `.env` and set required variables:

```bash
# Required - Generate with: openssl rand -hex 32
SECRET_KEY=your-secret-key-here

# Optional - OIDC Configuration
OIDC_ENABLED=false
# OIDC_PROVIDER=keycloak
# OIDC_CLIENT_ID=erpnext
# OIDC_CLIENT_SECRET=your-client-secret
# OIDC_REDIRECT_URI=https://erp.yourdomain.com/auth/login
```

### 3. Deploy with Docker Compose

```bash
docker compose -f docker-compose.erpnext.prod.yml up -d
```

### 4. Access ERPNext

Open your browser and navigate to `http://localhost:8080`

Default admin credentials:
- **Username**: Administrator
- **Password**: Set via `ADMIN_PASSWORD` in `.env`

---

## Docker Images

### Available Images

| Image | Description | Tags |
|-------|-------------|------|
| `ghcr.io/<owner>/erpnext` | ERPNext backend with OIDC support | `latest`, `v15`, `sha-<commit>` |
| `ghcr.io/<owner>/erpnext-nginx` | Nginx reverse proxy | `latest`, `v15`, `sha-<commit>` |

### Pull Images

```bash
docker pull ghcr.io/<owner>/erpnext:latest
docker pull ghcr.io/<owner>/erpnext-nginx:latest
```

---

## OIDC Authentication Setup

### Enable OIDC

Set the following in your `.env` file:

```bash
OIDC_ENABLED=true
OIDC_PROVIDER=keycloak  # Options: keycloak, google, auth0, azure, okta
OIDC_CLIENT_ID=erpnext
OIDC_CLIENT_SECRET=<your-client-secret>
OIDC_REDIRECT_URI=https://erp.yourdomain.com/auth/login
OIDC_SCOPE=openid profile email
```

### Provider Examples

#### Keycloak

```bash
OIDC_PROVIDER=keycloak
OIDC_ISSUER_URL=https://auth.yourdomain.com/realms/erpnext
OIDC_CLIENT_ID=erpnext
OIDC_CLIENT_SECRET=<keycloak-client-secret>
```

#### Google OAuth

```bash
OIDC_PROVIDER=google
OIDC_CLIENT_ID=<google-client-id>.apps.googleusercontent.com
OIDC_CLIENT_SECRET=<google-client-secret>
OIDC_SCOPE=openid profile email
```

#### Auth0

```bash
OIDC_PROVIDER=auth0
OIDC_ISSUER_URL=https://<your-auth0-domain>.auth0.com/
OIDC_CLIENT_ID=<auth0-client-id>
OIDC_CLIENT_SECRET=<auth0-client-secret>
```

See `docker/erpnext/README.md` for detailed OIDC configuration.

---

## CI/CD Pipeline

The repository includes a GitHub Actions workflow (`.github/workflows/build-push-setup.yml`) that:

1. **Validates** Docker Compose configuration and required files
2. **Builds** ERPNext and Nginx images with metadata tagging
3. **Pushes** images to GHCR on main branch or version tags
4. **Sets up** deployment instructions

### Workflow Triggers

- Push to `main` branch
- Version tags (`v*.*.*`)
- Manual trigger via GitHub Actions UI

### Required Secrets

Configure these in your GitHub repository settings:

| Secret | Description | Required |
|--------|-------------|----------|
| `GITHUB_TOKEN` | Auto-provided by GitHub | ✅ |
| `SECRET_KEY` | ERPNext secret key | ✅ (for build args) |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OIDC_ENABLED` | Enable OIDC authentication | `false` |

---

## Directory Structure

```
.
├── .env.example                    # Development environment template
├── .env.production.example         # Production environment template
├── .github/
│   └── workflows/
│       └── build-push-setup.yml    # CI/CD pipeline
├── docker/
│   ├── erpnext/
│   │   ├── Dockerfile              # ERPNext image definition
│   │   ├── configure-oidc.py       # OIDC auto-configuration script
│   │   ├── production-entrypoint.sh # Container entrypoint
│   │   └── README.md               # Detailed documentation
│   └── nginx/
│       ├── Dockerfile              # Nginx image definition
│       └── nginx.conf              # Nginx configuration
├── docker-compose.erpnext.prod.yml # Production compose file
├── LICENSE
├── README.md                       # This file
└── SECURITY.md                     # Security policy
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Cryptographic secret for sessions | `openssl rand -hex 32` |
| `SITE_NAME` | ERPNext site name | `erp.example.com` |
| `DB_HOST` | MariaDB hostname | `mariadb` |
| `DB_ROOT_PASSWORD` | Database root password | `secure-password` |
| `ADMIN_PASSWORD` | Admin user password | `admin-secure-password` |

### Optional (OIDC)

| Variable | Description | Default |
|----------|-------------|---------|
| `OIDC_ENABLED` | Enable OIDC authentication | `false` |
| `OIDC_PROVIDER` | OIDC provider name | - |
| `OIDC_CLIENT_ID` | OAuth2 client ID | - |
| `OIDC_CLIENT_SECRET` | OAuth2 client secret | - |
| `OIDC_REDIRECT_URI` | Callback URL | - |
| `OIDC_SCOPE` | OAuth2 scopes | `openid profile email` |

See `.env.production.example` for complete list.

---

## Security

- **Non-root containers**: All services run as unprivileged users
- **Pinned actions**: All GitHub Actions use SHA-pinned versions
- **Secret management**: Sensitive values via environment variables only
- **Network isolation**: Services communicate via internal Docker networks
- **Health checks**: Automatic service health monitoring

---

## Troubleshooting

### View Logs

```bash
docker compose -f docker-compose.erpnext.prod.yml logs -f erpnext
docker compose -f docker-compose.erpnext.prod.yml logs -f nginx
```

### Restart Services

```bash
docker compose -f docker-compose.erpnext.prod.yml restart
```

### Rebuild Images

```bash
docker compose -f docker-compose.erpnext.prod.yml build --no-cache
```

### Check OIDC Configuration

```bash
docker compose -f docker-compose.erpnext.prod.yml exec erpnext cat /home/frappe/frappe-bench/sites/site_config.json | grep oidc
```

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Support

- 📧 Issues: [GitHub Issues](../../issues)
- 📖 Documentation: `docker/erpnext/README.md`
- 🔒 Security: See [SECURITY.md](SECURITY.md)

---

**Built with ERPNext v15 • Docker • OIDC**
