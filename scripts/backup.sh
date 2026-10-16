#!/usr/bin/env bash
# Consistent, encrypted PostgreSQL backup for ERP03.
#
# Usage:
#   DATABASE_URL=postgresql+asyncpg://... BACKUP_DIR=/backups ./scripts/backup.sh
#
# Produces one compressed dump plus a SHA-256 checksum per run, encrypts the
# dump when `age` or `gpg` is available, and prunes backups older than
# RETENTION_DAYS. Backups must land on storage that is not the database host;
# point BACKUP_DIR at a mounted volume or object-storage sync target.
set -Eeuo pipefail

: "${DATABASE_URL:?DATABASE_URL must be set}"
: "${BACKUP_DIR:?BACKUP_DIR must be set (a path outside the database host)}"
: "${RETENTION_DAYS:=30}"

log() { printf '[backup] %s\n' "$*"; }

command -v pg_dump >/dev/null || { echo "pg_dump is required" >&2; exit 2; }
mkdir -p "$BACKUP_DIR"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
dump_file="${BACKUP_DIR}/erp03-${timestamp}.sql.gz"
checksum_file="${dump_file}.sha256"

# asyncpg URLs are not understood by pg_dump; rewrite them for libpq.
libpq_url="${DATABASE_URL/postgresql+asyncpg:/postgresql:}"

log "Dumping database to ${dump_file}"
pg_dump --no-owner --no-privileges "$libpq_url" | gzip -9 > "$dump_file"

sha256sum "$dump_file" > "$checksum_file"
log "Recorded checksum $(cut -d' ' -f1 < "$checksum_file")"

schema_revision="$(psql "$libpq_url" -Atc 'SELECT version_num FROM alembic_version LIMIT 1' || echo unknown)"
log "Schema revision at backup time: ${schema_revision}"
printf '%s\n' "$schema_revision" > "${dump_file}.schema-revision"

encrypted=0
if command -v age >/dev/null; then
  age --encrypt --recipient "${AGE_RECIPIENT:?AGE_RECIPIENT must be set when age is available}" \
    "$dump_file" > "${dump_file}.age" \
    && mv "${dump_file}.age" "$dump_file" \
    && encrypted=1
elif command -v gpg >/dev/null && [[ -n "${GPG_RECIPIENT:-}" ]]; then
  gpg --batch --yes --trust-model always --recipient "$GPG_RECIPIENT" \
    --output "${dump_file}.gpg" --encrypt "$dump_file" \
    && mv "${dump_file}.gpg" "$dump_file" \
    && encrypted=1
fi

if [[ "$encrypted" -eq 1 ]]; then
  sha256sum "$dump_file" > "$checksum_file"
  log "Encrypted backup at rest"
else
  log "WARNING: no age/gpg recipient configured; storing an unencrypted dump" >&2
fi

log "Pruning backups older than ${RETENTION_DAYS} days"
find "$BACKUP_DIR" -name 'erp03-*.sql.gz*' -mtime "+${RETENTION_DAYS}" -delete

log "Backup complete: ${dump_file}"
