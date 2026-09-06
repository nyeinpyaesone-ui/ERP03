#!/usr/bin/env bash
###############################################################################
# ERP03 — Secret Rotation Script
# Usage: ./scripts/rotate-secrets.sh [--dry-run]
# Rotates production secrets securely
###############################################################################
set -Eeuo pipefail

DRY_RUN="${1:-}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SECRETS_DIR="$(dirname "$0")/../secrets"

generate_secure_secret() {
    openssl rand -hex 32
}

generate_secure_password() {
    openssl rand -base64 24 | tr -dc 'a-zA-Z0-9!@#$%^&*' | head -c 24
}

echo "=== ERP03 Secret Rotation ==="
echo "Timestamp: $TIMESTAMP"
echo "Secrets Directory: $SECRETS_DIR"
echo ""

# Generate new secrets
NEW_JWT_SECRET=$(generate_secure_secret)
NEW_DB_PASSWORD=$(generate_secure_password)
NEW_REDIS_PASSWORD=$(generate_secure_password)
NEW_APP_SECRET=$(generate_secure_secret)

if [[ "$DRY_RUN" == "--dry-run" ]]; then
    echo "[DRY RUN] Would generate new secrets:"
    echo "  JWT_SECRET: ${NEW_JWT_SECRET:0:8}..."
    echo "  DB_PASSWORD: ********"
    echo "  REDIS_PASSWORD: ********"
    echo "  APP_SECRET: ${NEW_APP_SECRET:0:8}..."
    echo ""
    echo "No files were modified."
else
    echo "Generating new secrets..."
    
    # Ensure secrets directory exists
    mkdir -p "$SECRETS_DIR"
    
    # Create new secret files with .new extension
    echo "$NEW_JWT_SECRET" > "$SECRETS_DIR/jwt_secret.txt.new"
    echo "$NEW_DB_PASSWORD" > "$SECRETS_DIR/db_password.txt.new"
    echo "$NEW_REDIS_PASSWORD" > "$SECRETS_DIR/redis_password.txt.new"
    echo "$NEW_APP_SECRET" > "$SECRETS_DIR/app_secret.txt.new"
    
    # Set secure permissions
    chmod 600 "$SECRETS_DIR"/*.new
    
    echo ""
    echo "✓ New secrets generated successfully"
    echo ""
    echo "Next steps:"
    echo "1. Review the new secret files in $SECRETS_DIR"
    echo "2. Update environment variables in your deployment configuration"
    echo "3. Update GitHub Secrets (Settings → Secrets and variables → Actions)"
    echo "4. Restart all services to apply new secrets"
    echo "5. Once verified, move .new files to replace old secrets:"
    echo "   mv $SECRETS_DIR/*.new $SECRETS_DIR/"
    echo ""
    echo "⚠️  WARNING: After rotation, invalidate all existing JWT tokens!"
fi
