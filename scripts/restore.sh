#!/usr/bin/env bash
set -euo pipefail

# ERP03 Database Restore Script
# Usage: ./scripts/restore.sh <backup_file> [--verify-only]
# WARNING: This will overwrite the target database. Use only in isolated environments.

BACKUP_FILE="${1:?Usage: restore.sh <backup_file> [--verify-only]}"
VERIFY_ONLY="${2:-}"

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "==> Verifying backup file: $BACKUP_FILE"
if [[ -f "$BACKUP_FILE.sha256" ]]; then
    sha256sum -c "$BACKUP_FILE.sha256" || { echo "ERROR: Checksum mismatch"; exit 1; }
    echo "   checksum: OK"
fi
gunzip -t "$BACKUP_FILE" && echo "   gzip integrity: OK"

if [[ "$VERIFY_ONLY" == "--verify-only" ]]; then
    echo "==> Verify-only mode: listing backup contents"
    gunzip -c "$BACKUP_FILE" | pg_restore --list - | head -20
    echo "==> Verification complete (no restore performed)"
    exit 0
fi

echo "==> WARNING: This will overwrite the target database"
echo "    Target: ${DATABASE_URL:-postgresql+asyncpg://erp03:erp03@localhost:5432/erp03}"
read -p "Type 'RESTORE' to confirm: " CONFIRM
if [[ "$CONFIRM" != "RESTORE" ]]; then
    echo "Aborted."
    exit 1
fi

echo "==> Dropping and recreating database"
psql -U erp03 -d postgres -c "DROP DATABASE IF EXISTS erp03;" || true
psql -U erp03 -d postgres -c "CREATE DATABASE erp03;"

echo "==> Restoring from backup"
gunzip -c "$BACKUP_FILE" | pg_restore --no-owner --no-acl -U erp03 -d erp03

echo "==> Verifying restore"
psql -U erp03 -d erp03 -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"
psql -U erp03 -d erp03 -c "SELECT version_num FROM alembic_version;" 2>/dev/null || echo "   (no alembic_version table yet)"

echo "==> Restore complete"
