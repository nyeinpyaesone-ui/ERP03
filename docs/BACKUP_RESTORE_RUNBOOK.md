# ERP03 Backup and Restore Runbook

## Backup
- Use PostgreSQL `pg_dump` for transactional recovery.
- Store backups outside the database host.
- Encrypt backup storage at rest.
- Record backup timestamp, schema revision, and checksum.

## Restore verification
1. Restore into an isolated PostgreSQL instance.
2. Run `alembic current`.
3. Run readiness checks.
4. Run integration and transaction tests.
5. Record restore duration and result.

Production RPO/RTO values must be approved before deployment; this repository does not invent provider-specific values.
