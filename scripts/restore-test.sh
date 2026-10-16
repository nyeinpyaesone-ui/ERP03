#!/usr/bin/env bash
# Restore a backup into an isolated database and prove it works.
#
# Usage:
#   RESTORE_URL=postgresql://erp03:pw@127.0.0.1:5433/erp03_restore \
#   BACKUP_FILE=/backups/erp03-20261016T120000Z.sql.gz \
#   ./scripts/restore-test.sh
#
# A restore is only real once it has been restored. This script is the
# verification half of docs/BACKUP_RESTORE_RUNBOOK.md: it restores a dump into
# a throwaway database, runs migrations, and executes the integration suite
# against the restored data.
set -Eeuo pipefail

: "${RESTORE_URL:?RESTORE_URL must point at an isolated database}"
: "${BACKUP_FILE:?BACKUP_FILE must point at an existing dump}"
: "${SKIP_TESTS:=0}"

log() { printf '[restore] %s\n' "$*"; }

[[ -f "$BACKUP_FILE" ]] || { echo "backup file not found: $BACKUP_FILE" >&2; exit 2; }
[[ -f "${BACKUP_FILE}.sha256" ]] && {
  log "Verifying checksum"
  sha256sum --check "${BACKUP_FILE}.sha256"
}

libpq_url="${RESTORE_URL/postgresql+asyncpg:/postgresql:}"
root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log "Restoring ${BACKUP_FILE} into ${RESTORE_URL}"
if [[ "$BACKUP_FILE" == *.age ]]; then
  age --decrypt --identity "${AGE_IDENTITY:?AGE_IDENTITY required to decrypt}" "$BACKUP_FILE" | gunzip | psql "$libpq_url" -v ON_ERROR_STOP=1 -q
elif [[ "$BACKUP_FILE" == *.gpg ]]; then
  gpg --batch --quiet --decrypt "$BACKUP_FILE" | gunzip | psql "$libpq_url" -v ON_ERROR_STOP=1 -q
else
  gunzip -c "$BACKUP_FILE" | psql "$libpq_url" -v ON_ERROR_STOP=1 -q
fi

cd "$root_dir/ERP-BACKEND"
log "Schema revision after restore"
DATABASE_URL="$RESTORE_URL" alembic current
DATABASE_URL="$RESTORE_URL" alembic upgrade head

if [[ "$SKIP_TESTS" != "1" ]]; then
  log "Running integration suite against restored data"
  DATABASE_URL="$RESTORE_URL" DATABASE_PATH="${DATABASE_PATH:-/tmp/erp03-restore.sqlite3}" \
    python -m pytest -q
else
  log "SKIP_TESTS=1 — migrations verified, tests skipped"
fi

log "Restore verification passed for ${BACKUP_FILE}"
