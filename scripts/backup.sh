#!/usr/bin/env bash
set -euo pipefail

# ERP03 Database Backup Script
# Usage: ./scripts/backup.sh [backup_dir]
# Environment: DATABASE_URL, BACKUP_DIR, BACKUP_RETENTION_DAYS

BACKUP_DIR="${BACKUP_DIR:-/data/backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_FILE="$BACKUP_DIR/erp03-$TIMESTAMP.sql.gz"
CHECKSUM_FILE="$BACKUP_FILE.sha256"

mkdir -p "$BACKUP_DIR"

echo "==> Creating backup: $BACKUP_FILE"
pg_dump --no-owner --no-acl --format=custom -U erp03 -d erp03 | gzip > "$BACKUP_FILE"

echo "==> Computing checksum"
sha256sum "$BACKUP_FILE" > "$CHECKSUM_FILE"

echo "==> Verifying backup integrity"
gunzip -t "$BACKUP_FILE" && echo "   gzip integrity: OK"
sha256sum -c "$CHECKSUM_FILE" && echo "   checksum: OK"

# Verify restore capability (dry-run: list contents)
echo "==> Verifying backup contents"
pg_restore --list "$BACKUP_FILE" > /dev/null 2>&1 && echo "   restore list: OK" || \
  (gunzip -c "$BACKUP_FILE" | pg_restore --list - > /dev/null 2>&1 && echo "   restore list: OK")

echo "==> Backup complete: $BACKUP_FILE"
echo "    Size: $(du -h "$BACKUP_FILE" | cut -f1)"
echo "    Checksum: $(cat "$CHECKSUM_FILE")"

# Retention cleanup
echo "==> Cleaning up backups older than $BACKUP_RETENTION_DAYS days"
find "$BACKUP_DIR" -name "erp03-*.sql.gz" -mtime +"$BACKUP_RETENTION_DAYS" -delete
find "$BACKUP_DIR" -name "erp03-*.sql.gz.sha256" -mtime +"$BACKUP_RETENTION_DAYS" -delete
echo "==> Retention cleanup complete"
