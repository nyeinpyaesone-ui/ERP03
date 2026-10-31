#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/data/backups}"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_FILE="$BACKUP_DIR/erp03-$TIMESTAMP.sql.gz"

echo "Creating backup $BACKUP_FILE"
pg_dump -U erp03 -d erp03 | gzip > "$BACKUP_FILE"

echo "Verifying backup"
gunzip -t "$BACKUP_FILE" && echo "Backup integrity OK"

echo "Backup complete: $BACKUP_FILE"
