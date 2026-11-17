# ERP03 Rollback Runbook

1. Stop promotion on failed smoke or health checks.
2. Identify the last known-good immutable image and commit.
3. Roll back application workloads after confirming database compatibility.
4. Never downgrade database schema automatically.
5. For incompatible migrations, follow the migration-specific recovery procedure and restore only from a verified backup when required.
6. Re-run health, readiness, and critical transaction smoke tests.
7. Record incident ID, versions, migration revision, operator, and outcome.
