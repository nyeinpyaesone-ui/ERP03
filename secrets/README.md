# Runtime Secrets Management for ERP03 Production

## Overview

Production secret files are intentionally not committed to version control.
This directory contains templates and documentation for secure secret management.

## Quick Start - Generate Production Secrets

Run the secure generation script on your production deployment host:

```bash
./scripts/generate-secrets.sh
```

This script will:
1. Generate cryptographically secure passwords and secrets using OpenSSL
2. Create the required secret files in this directory with proper permissions (600)
3. Output the generated values for you to store in a secure vault
4. Create a template `.env.production` file content

**IMPORTANT**: Save the output immediately to a secure vault (AWS Secrets Manager, HashiCorp Vault, etc.)

## Required Secret Files

After running the generation script, these files will be created:

- `secrets/postgres_password.txt` — PostgreSQL password only (generated with `openssl rand -base64 24`)
- `secrets/database_url.txt` — Complete SQLAlchemy PostgreSQL URL with credentials
- `secrets/secret_key.txt` — Application signing key (64 hex characters from `openssl rand -hex 32`)

## Manual Creation (Alternative)

If you prefer to create secrets manually:

```bash
mkdir -p secrets

# Generate PostgreSQL password
openssl rand -base64 24 | tr -d '\n' > secrets/postgres_password.txt
chmod 600 secrets/postgres_password.txt

# Generate DATABASE_URL (replace <PASSWORD> with the generated password)
echo "postgresql+asyncpg://erp03_prod_user:<PASSWORD>@db:5432/erp03_prod" > secrets/database_url.txt
chmod 600 secrets/database_url.txt

# Generate SECRET_KEY
openssl rand -hex 32 | tr -d '\n' > secrets/secret_key.txt
chmod 600 secrets/secret_key.txt
```

## Docker Compose Production Usage

Start production services with secrets:

```bash
docker compose -f docker-compose.yml -f compose.production.yml up -d --build
```

The production overlay (`compose.production.yml`):
- Removes development bind mounts and reload mode
- Does not expose PostgreSQL to external networks
- Injects `DATABASE_URL` and `SECRET_KEY` through Docker secrets
- Uses read-only secret files at `/run/secrets/<name>`

## Environment Variables (.env.production)

For Docker Compose production, also create `.env.production` (not committed):

```bash
# Copy from .env.production.example and update with generated values
cp .env.production.example .env.production
```

Required variables:
- `DB_USER` — PostgreSQL username
- `DB_PASSWORD` — PostgreSQL password (same as in postgres_password.txt)
- `DB_NAME` — PostgreSQL database name
- `REDIS_PASSWORD` — Redis password
- `SECRET_KEY` — Application secret key
- `APP_SECRET` — Additional application secret
- `CORS_ORIGINS` — Allowed CORS origins (your production domain)

## Kubernetes Secret Management

For Kubernetes deployments, use External Secrets Operator or sealed secrets:

```yaml
# Reference secrets via ExternalSecret resources
# See infra/k8s/base/external-secrets.yaml
```

## Security Best Practices

1. **Never commit** real credentials, `.env` files, or files under `secrets/`
2. **Rotate secrets** every 90-180 days
3. **Use different secrets** for each environment (dev, staging, production)
4. **Store backups** of secrets in a secure vault
5. **Restrict access** to secret files (chmod 600)
6. **Audit access** to production secrets regularly

## Secret File Permissions

All secret files must have restricted permissions:

```bash
chmod 600 secrets/*.txt
chown root:root secrets/*.txt  # Or appropriate owner
```

## Troubleshooting

### Permission Denied Errors

Ensure secret files have correct permissions:
```bash
ls -la secrets/
# Should show: -rw------- (600)
```

### Missing Secret Files

Regenerate using the script or create manually as shown above.

### Docker Cannot Read Secrets

Verify the secrets are properly referenced in `compose.production.yml` and the files exist.
