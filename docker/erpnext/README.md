# ERPNext Docker Image with OIDC Authentication Support

## Overview

This directory contains the Docker configuration for building an ERPNext production image with optional OpenID Connect (OIDC) authentication support. The image is built on top of the official `frappe/erpnext:v15.120.0` base image and includes:

- **OIDC/OAuth2 Integration**: Configurable single sign-on (SSO) support
- **Production-ready Entrypoint**: Automated database and Redis connection validation
- **Security Hardening**: Minimal dependencies, non-root user execution
- **Multi-provider Support**: Works with Keycloak, Google, Auth0, Azure AD, Okta, and other OIDC providers

## Directory Structure

```
docker/erpnext/
├── Dockerfile                  # Main Docker image definition
├── configure-oidc.py          # OIDC configuration script
└── production-entrypoint.sh   # Container startup script
```

## Features

### 1. OIDC Authentication

The image supports optional OIDC authentication that can be enabled via environment variables. When enabled, the container automatically configures ERPNext to use your OIDC provider for user authentication.

**Supported Providers:**
- Keycloak
- Google OAuth2
- Auth0
- Azure Active Directory
- Okta
- Any generic OIDC-compliant provider

### 2. Automatic Configuration

On container startup, if OIDC is enabled, the `configure-oidc.py` script:
- Reads OIDC settings from environment variables
- Updates the site_config.json with OAuth/OIDC configuration
- Configures ERPNext's social login integration
- Validates required endpoints and credentials

### 3. Health Checks

The entrypoint script performs comprehensive health checks:
- Database connectivity (MariaDB/MySQL)
- Redis cache availability
- Redis queue availability
- Redis Socket.IO availability
- Automatic retry with exponential backoff

## Building the Image

### Local Build

```bash
docker build -t erpnext:production -f docker/erpnext/Dockerfile .
```

### With Build Arguments

```bash
docker build \
  -t erpnext:production \
  -f docker/erpnext/Dockerfile \
  --build-arg VERSION=1.0.0 \
  .
```

## Usage

### Basic Deployment (Without OIDC)

```yaml
services:
  erpnext:
    image: erpnext:production
    environment:
      SITE_NAME: erp.example.com
      DB_HOST: mariadb
      DB_PORT: "3306"
      DB_ROOT_USER: root
      DB_ROOT_PASSWORD: secure_password
      ADMIN_PASSWORD: admin_secure_password
      REDIS_CACHE: redis://redis-cache:6379
      REDIS_QUEUE: redis://redis-queue:6379
      REDIS_SOCKETIO: redis://redis-socketio:6379
    volumes:
      - erpnext_sites:/home/frappe/frappe-bench/sites
      - erpnext_logs:/home/frappe/frappe-bench/logs
```

### With OIDC Authentication (Keycloak Example)

```yaml
services:
  erpnext:
    image: erpnext:production
    environment:
      # Basic Configuration
      SITE_NAME: erp.example.com
      DB_HOST: mariadb
      DB_ROOT_PASSWORD: secure_password
      ADMIN_PASSWORD: admin_secure_password
      REDIS_CACHE: redis://redis-cache:6379
      REDIS_QUEUE: redis://redis-queue:6379
      REDIS_SOCKETIO: redis://redis-socketio:6379

      # OIDC Configuration
      OIDC_ENABLED: "true"
      OIDC_PROVIDER: keycloak
      OIDC_CLIENT_ID: erpnext-client
      OIDC_CLIENT_SECRET: ${KEYCLOAK_CLIENT_SECRET}
      OIDC_REDIRECT_URI: https://erp.example.com/api/method/frappe.integrations.oauth2_logins.login/keycloak
      OIDC_SCOPE: openid profile email
      OIDC_AUTHORIZATION_URL: https://auth.example.com/realms/myrealm/protocol/openid-connect/auth
      OIDC_TOKEN_URL: https://auth.example.com/realms/myrealm/protocol/openid-connect/token
      OIDC_USERINFO_URL: https://auth.example.com/realms/myrealm/protocol/openid-connect/userinfo
      OIDC_JWKS_URL: https://auth.example.com/realms/myrealm/protocol/openid-connect/certs
      OIDC_ISSUER: https://auth.example.com/realms/myrealm
```

### With Google OAuth

```yaml
environment:
  OIDC_ENABLED: "true"
  OIDC_PROVIDER: google
  OIDC_CLIENT_ID: ${GOOGLE_CLIENT_ID}
  OIDC_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET}
  OIDC_REDIRECT_URI: https://erp.example.com/api/method/frappe.integrations.oauth2_logins.login/google
  OIDC_SCOPE: openid profile email
  OIDC_AUTHORIZATION_URL: https://accounts.google.com/o/oauth2/v2/auth
  OIDC_TOKEN_URL: https://oauth2.googleapis.com/token
  OIDC_USERINFO_URL: https://www.googleapis.com/oauth2/v3/userinfo
  OIDC_JWKS_URL: https://www.googleapis.com/oauth2/v3/certs
  OIDC_ISSUER: https://accounts.google.com
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SITE_NAME` | Site domain name | `erp.example.com` |
| `DB_HOST` | Database host | `mariadb` |
| `DB_ROOT_PASSWORD` | Database root password | `secure_password` |
| `ADMIN_PASSWORD` | Admin user password | `admin_secure_password` |
| `REDIS_CACHE` | Redis cache URL | `redis://redis-cache:6379` |
| `REDIS_QUEUE` | Redis queue URL | `redis://redis-queue:6379` |
| `REDIS_SOCKETIO` | Redis Socket.IO URL | `redis://redis-socketio:6379` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PORT` | `3306` | Database port |
| `DB_ROOT_USER` | `root` | Database root username |
| `GUNICORN_WORKERS` | `2` | Number of Gunicorn workers |
| `GUNICORN_THREADS` | `4` | Number of threads per worker |
| `GUNICORN_TIMEOUT` | `120` | Gunicorn timeout in seconds |
| `QUEUE` | `long,default,short` | Worker queues to process |

### OIDC Variables (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `OIDC_ENABLED` | `false` | Enable OIDC authentication (`true`/`false`) |
| `OIDC_PROVIDER` | `generic` | Provider name (keycloak, google, auth0, etc.) |
| `OIDC_CLIENT_ID` | - | OAuth2 Client ID (required if OIDC enabled) |
| `OIDC_CLIENT_SECRET` | - | OAuth2 Client Secret (required if OIDC enabled) |
| `OIDC_REDIRECT_URI` | - | OAuth2 Redirect URI (required if OIDC enabled) |
| `OIDC_SCOPE` | `openid profile email` | OAuth2 scopes (space-separated) |
| `OIDC_AUTHORIZATION_URL` | - | Authorization endpoint URL |
| `OIDC_TOKEN_URL` | - | Token endpoint URL |
| `OIDC_USERINFO_URL` | - | Userinfo endpoint URL |
| `OIDC_JWKS_URL` | - | JWKS endpoint URL for token validation |
| `OIDC_ISSUER` | - | Issuer identifier |

## OIDC Provider Setup

### Keycloak

1. Create a new realm in Keycloak
2. Create a new client with:
   - Client ID: `erpnext-client`
   - Client Protocol: `openid-connect`
   - Access Type: `confidential`
   - Valid Redirect URIs: `https://erp.example.com/*`
   - Web Origins: `https://erp.example.com`
3. Get client secret from Credentials tab
4. Configure environment variables with Keycloak URLs

### Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `https://erp.example.com/api/method/frappe.integrations.oauth2_logins.login/google`
5. Note Client ID and Client Secret

### Auth0

1. Create a new application in Auth0 dashboard
2. Select application type: Regular Web Application
3. Configure:
   - Allowed Callback URLs: `https://erp.example.com/api/method/frappe.integrations.oauth2_logins.login/auth0`
   - Allowed Logout URLs: `https://erp.example.com`
4. Get Client ID, Client Secret, and Domain from Settings

### Azure Active Directory

1. Register a new application in Azure Portal
2. Configure redirect URIs:
   - Platform: Web
   - Redirect URI: `https://erp.example.com/api/method/frappe.integrations.oauth2_logins.login/azure`
3. Create a client secret
4. Note Tenant ID, Client ID, and Client Secret

## Volumes

| Volume | Mount Point | Purpose |
|--------|-------------|---------|
| `erpnext_sites` | `/home/frappe/frappe-bench/sites` | Site configurations and data |
| `erpnext_logs` | `/home/frappe/frappe-bench/logs` | Application logs |

## Ports

| Port | Protocol | Purpose |
|------|----------|---------|
| 8000 | HTTP | Gunicorn web server |
| 9000 | WebSocket | Socket.IO for real-time features |

## Security Considerations

1. **Never commit secrets**: Use Docker secrets or environment files
2. **Use HTTPS in production**: Always use TLS for OIDC redirect URIs
3. **Rotate client secrets**: Regularly rotate OAuth client secrets
4. **Restrict redirect URIs**: Only allow specific redirect URIs in your OIDC provider
5. **Use strong admin passwords**: Generate secure passwords for initial admin account
6. **Enable container security**: Use `init: true`, read-only filesystems where possible

## Troubleshooting

### OIDC Not Working

1. Check if OIDC_ENABLED is set to `true`
2. Verify all required OIDC environment variables are set
3. Check container logs for OIDC configuration errors:
   ```bash
   docker logs <container-name> | grep oidc
   ```
4. Ensure redirect URI matches exactly between provider and configuration
5. Verify network connectivity to OIDC provider endpoints

### Database Connection Issues

1. Verify DB_HOST and DB_PORT are correct
2. Check database is running and accessible
3. Ensure DB_ROOT_PASSWORD is correct
4. Check firewall rules between containers

### Redis Connection Issues

1. Verify Redis URLs are correctly formatted
2. Check Redis services are healthy
3. Ensure network connectivity between containers

## Testing

### Test OIDC Configuration Script

```bash
# Run locally with test values
docker run --rm \
  -e OIDC_ENABLED=true \
  -e OIDC_PROVIDER=keycloak \
  -e OIDC_CLIENT_ID=test-client \
  -e OIDC_CLIENT_SECRET=test-secret \
  -e OIDC_REDIRECT_URI=http://localhost:8080/callback \
  -v $(pwd)/test-site-config.json:/home/frappe/frappe-bench/sites/site1.local/site_config.json \
  erpnext:production \
  python /opt/scripts/configure-oidc.py
```

### Validate Docker Compose Configuration

```bash
docker compose -f docker-compose.erpnext.prod.yml config
```

## License

This Docker configuration is part of the ERP Solution project and follows the same license terms.

## Support

For issues or questions:
1. Check the [FAQ](../../docs/FAQ.md)
2. Review [Deployment Checklist](../../DEPLOYMENT_CHECKLIST.md)
3. Open an issue on GitHub
