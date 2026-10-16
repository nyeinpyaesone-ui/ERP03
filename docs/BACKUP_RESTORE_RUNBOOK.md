# ERP03 Backup and Restore Runbook

## Backup

`scripts/backup.sh` produces the required artefacts:

```bash
DATABASE_URL="$DATABASE_URL" BACKUP_DIR=/backups/erp03 ./scripts/backup.sh
```

Per run it writes:
- `erp03-<timestamp>.sql.gz` — compressed `pg_dump` (encrypted with `age` or
  `gpg` when a recipient is configured)
- `erp03-<timestamp>.sql.gz.sha256` — checksum to detect corruption in transit
  or at rest
- `erp03-<timestamp>.sql.gz.schema-revision` — Alembic revision at dump time,
  so a restore can prove which schema it will produce

Requirements:
- Run on a schedule (at least daily) from a host that is **not** the database
  host, and land the files on separate storage.
- Storage must be encrypted at rest; the script refuses to stay quiet when no
  encryption tool is configured.
- Retention defaults to 30 days (`RETENTION_DAYS`); production retention is
  35 days (see `infra/terraform/modules/database`).

## Restore verification

A backup is only real once it has been restored:

```bash
RESTORE_URL=postgresql://erp03:pw@127.0.0.1:5433/erp03_restore \
BACKUP_FILE=/backups/erp03-<timestamp>.sql.gz \
./scripts/restore-test.sh
```

The script verifies the checksum, restores into an isolated database, runs
`alembic current` and `alembic upgrade head`, then executes the test suite
against the restored data.

Verification schedule:
- Monthly, or after any migration that changes data in place.
- Before any major release that includes a migration.

## Recovery

1. Declare the incident and target recovery point (RPO decision).
2. Restore the chosen backup into the production database instance using the
   isolated-restore procedure above as a dry run first.
3. Confirm the schema revision matches the expected application build.
4. Deploy the application build that matches the restored schema.
5. Run smoke tests and verify transaction integrity
   (`docs/TRANSACTION_INTEGRITY.md`).
6. Record restore duration, revision and operator evidence.

Production RPO/RTO values must be approved before deployment; this repository
does not invent provider-specific values.
