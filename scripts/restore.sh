#!/usr/bin/env bash
###############################################################################
# ERP03 — PostgreSQL restore helper
# Usage: ./scripts/restore.sh <backup.sql|backup.sql.gpg>
# WARNING: restore replaces data in the target database. Verify the target first.
###############################################################################
set -Eeuo pipefail

BACKUP_FILE="${1:?Usage: ./scripts/restore.sh <backup.sql|backup.sql.gpg>}"
DB_USER="${DB_USER:-erp}"
DB_NAME="${DB_NAME:-erpo3}"

[[ -f "${BACKUP_FILE}" ]] || { echo "Backup file not found: ${BACKUP_FILE}" >&2; exit 1; }

if [[ "${BACKUP_FILE}" == *.gpg ]]; then
  command -v gpg >/dev/null 2>&1 || { echo "gpg is required for encrypted backups." >&2; exit 1; }
  TMP_SQL="$(mktemp)"
  trap 'rm -f "${TMP_SQL}"' EXIT
  gpg --decrypt --output "${TMP_SQL}" "${BACKUP_FILE}"
  SQL_FILE="${TMP_SQL}"
else
  SQL_FILE="${BACKUP_FILE}"
fi

if docker compose ps postgres >/dev/null 2>&1; then
  echo "Restoring into compose PostgreSQL service..."
  docker compose exec -T postgres psql -U "${DB_USER}" -d "${DB_NAME}" < "${SQL_FILE}"
elif command -v psql >/dev/null 2>&1; then
  : "${DATABASE_URL:?DATABASE_URL is required when psql is used directly}"
  psql "${DATABASE_URL}" < "${SQL_FILE}"
else
  echo "ERROR: PostgreSQL is unavailable (no compose postgres service and no psql)." >&2
  exit 1
fi

printf 'Restore completed from %s\n' "${BACKUP_FILE}"
