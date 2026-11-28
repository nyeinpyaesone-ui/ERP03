#!/bin/bash
# Secure Secret Generation Script for ERP03 Production
# This script generates cryptographically secure secrets for production deployment
# Run this script ONCE during initial production setup and store outputs securely

set -euo pipefail

SECRETS_DIR="./secrets"

echo "=== ERP03 Production Secret Generation ==="
echo ""

# Create secrets directory if it doesn't exist
mkdir -p "$SECRETS_DIR"

# Generate PostgreSQL password (24 characters, base64)
POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -d '\n')
echo "$POSTGRES_PASSWORD" > "$SECRETS_DIR/postgres_password.txt"
chmod 600 "$SECRETS_DIR/postgres_password.txt"
echo "✓ Generated PostgreSQL password"

# Generate Redis password (24 characters, base64)
REDIS_PASSWORD=$(openssl rand -base64 24 | tr -d '\n')
echo "✓ Generated Redis password"

# Generate JWT secret (64 hex characters)
JWT_SECRET=$(openssl rand -hex 32)
echo "✓ Generated JWT secret"

# Generate APP secret (64 hex characters)
APP_SECRET=$(openssl rand -hex 32)
echo "✓ Generated APP secret"

# Generate DATABASE_URL using the PostgreSQL password
DB_USER="erp03_prod_user"
DB_NAME="erp03_prod"
DATABASE_URL="postgresql+asyncpg://${DB_USER}:${POSTGRES_PASSWORD}@db:5432/${DB_NAME}"
echo "$DATABASE_URL" > "$SECRETS_DIR/database_url.txt"
chmod 600 "$SECRETS_DIR/database_url.txt"
echo "✓ Generated DATABASE_URL"

# Generate SECRET_KEY for application
echo "$JWT_SECRET" > "$SECRETS_DIR/secret_key.txt"
chmod 600 "$SECRETS_DIR/secret_key.txt"
echo "✓ Generated SECRET_KEY"

echo ""
echo "=== Secrets Generated Successfully ==="
echo ""
echo "IMPORTANT: Store these values in a secure vault immediately:"
echo ""
echo "  POSTGRES_PASSWORD: $POSTGRES_PASSWORD"
echo "  REDIS_PASSWORD:    $REDIS_PASSWORD"
echo "  JWT_SECRET:        $JWT_SECRET"
echo "  APP_SECRET:        $APP_SECRET"
echo ""
echo "Files created in $SECRETS_DIR/:"
echo "  - postgres_password.txt"
echo "  - database_url.txt"
echo "  - secret_key.txt"
echo ""
echo "These files are gitignored. Never commit actual secret values."
echo ""
echo "For Docker Compose production, also create .env.production with:"
cat << EOF

# =============================================================================
# PRODUCTION ENVIRONMENT VARIABLES (Copy to .env.production)
# DO NOT COMMIT THIS FILE
# =============================================================================
DB_USER=$DB_USER
DB_NAME=$DB_NAME
DB_PASSWORD=$POSTGRES_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD
SECRET_KEY=$JWT_SECRET
APP_SECRET=$APP_SECRET
CORS_ORIGINS=https://your-production-domain.com
ENVIRONMENT=production
LOG_LEVEL=INFO

EOF
