#!/usr/bin/env bash
###############################################################################
# ERP03 — Safe PostgreSQL backup
# Usage: ./scripts/backup.sh [output_dir]
# Required: pg_dump (or docker compose service "postgres")
# Optional: GPG_RECIPIENT for client-side encryption of the database dump.
###############################################################################
set -Eeuo pipefail

OUTPUT_DIR="${1:-./backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_PATH="${OUTPUT_DIR}/erp03_${TIMESTAMP}"
DB_USER="${DB_USER:-erp}"
DB_NAME="${DB_NAME:-erp03}"
GPG_RECIPIENT="${GPG_RECIPIENT:-}"

mkdir -p "${BACKUP_PATH}"

if docker compose ps postgres >/dev/null 2>&1; then
  echo "Backing up PostgreSQL from compose service..."
  docker compose exec -T postgres pg_dump -U "${DB_USER}" "${DB_NAME}" > "${BACKUP_PATH}/database.sql"
elif command -v pg_dump >/dev/null 2>&1; then
  : "${DATABASE_URL:?DATABASE_URL is required when pg_dump is used directly}"
  echo "Backing up PostgreSQL using pg_dump..."
  pg_dump "${DATABASE_URL}" > "${BACKUP_PATH}/database.sql"
else
  echo "ERROR: PostgreSQL is unavailable (no compose postgres service and no pg_dump)." >&2
  exit 1
fi

if [[ -n "${GPG_RECIPIENT}" ]]; then
  command -v gpg >/dev/null 2>&1 || { echo "ERROR: gpg is required for encrypted backups." >&2; exit 1; }
  gpg --batch --yes --trust-model always --recipient "${GPG_RECIPIENT}" \
      --output "${BACKUP_PATH}/database.sql.gpg" --encrypt "${BACKUP_PATH}/database.sql"
  rm -f "${BACKUP_PATH}/database.sql"
  DB_ARTIFACT="database.sql.gpg"
else
  echo "WARNING: GPG_RECIPIENT is not set; database dump is NOT encrypted." >&2
  DB_ARTIFACT="database.sql"
fi

cat > "${BACKUP_PATH}/manifest.txt" <<EOF
ERP03 backup
Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Version: $(git describe --tags --always 2>/dev/null || echo unknown)
Commit: $(git rev-parse HEAD 2>/dev/null || echo unknown)
Database artifact: ${DB_ARTIFACT}

Secrets and .env files are intentionally NOT included.
EOF

printf 'Backup complete: %s\n' "${BACKUP_PATH}"
