#!/usr/bin/env bash
###############################################################################
# ERP03 — backup/restore verification helper
# Usage: ./scripts/verify-backup-restore.sh <backup.sql|backup.sql.gpg>
# Verifies backup readability and performs a restore into the configured target.
###############################################################################
set -Eeuo pipefail

BACKUP_FILE="${1:?Usage: ./scripts/verify-backup-restore.sh <backup.sql|backup.sql.gpg>}"
VERIFY_ONLY="${VERIFY_ONLY:-false}"

[[ -f "${BACKUP_FILE}" ]] || { echo "Backup file not found: ${BACKUP_FILE}" >&2; exit 1; }

if [[ "${BACKUP_FILE}" == *.gpg ]]; then
  command -v gpg >/dev/null 2>&1 || { echo "gpg is required for encrypted backups." >&2; exit 1; }
  TMP_SQL="$(mktemp)"
  trap 'rm -f "${TMP_SQL}"' EXIT
  gpg --batch --decrypt --output "${TMP_SQL}" "${BACKUP_FILE}"
  SQL_FILE="${TMP_SQL}"
else
  SQL_FILE="${BACKUP_FILE}"
fi

command -v psql >/dev/null 2>&1 || { echo "psql is required for verification." >&2; exit 1; }
: "${DATABASE_URL:?DATABASE_URL is required for restore verification}"

# Parse the dump without modifying the target first.
pg_restore --version >/dev/null 2>&1 || true
if head -c 5 "${SQL_FILE}" | grep -q '^PGDMP'; then
  command -v pg_restore >/dev/null 2>&1 || { echo "pg_restore is required for custom-format backups." >&2; exit 1; }
  pg_restore --list "${SQL_FILE}" >/dev/null
else
  grep -qE '^(--|CREATE|SET|COPY|INSERT|BEGIN|ALTER|COMMENT|GRANT|REVOKE)' "${SQL_FILE}" || {
    echo "Backup does not look like a PostgreSQL SQL dump." >&2
    exit 1
  }
fi

if [[ "${VERIFY_ONLY}" == "true" ]]; then
  echo "Backup verification passed: ${BACKUP_FILE}"
  exit 0
fi

# Restore into the configured DATABASE_URL target; this is intentionally explicit
# so production cannot be overwritten accidentally by a default connection.
psql "${DATABASE_URL}" --set ON_ERROR_STOP=1 --single-transaction < "${SQL_FILE}"
echo "Backup restore verification passed: ${BACKUP_FILE}"
