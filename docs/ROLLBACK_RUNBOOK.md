# ERP03 Rollback Runbook

Rollback is executed by the `Rollback` workflow, never by hand-editing a
running cluster.

```bash
# Preferred: pin the last known-good immutable digest
gh workflow run rollback.yml \
  -f environment=production \
  -f mode=digest \
  -f backend_digest=ghcr.io/nyeinpyaesone-ui/erp03-backend@sha256:<known-good> \
  -f frontend_digest=ghcr.io/nyeinpyaesone-ui/erp03-frontend@sha256:<known-good> \
  -f incident_id=<incident-reference>

# Alternative: roll the Deployment back to its previous ReplicaSet revision
gh workflow run rollback.yml \
  -f environment=production -f mode=undo -f incident_id=<incident-reference>
```

## Procedure
1. Stop promotion on failed smoke or health checks — pause the release.
2. Identify the last known-good commit and digests from the previous
   deployment's workflow summary or `kubectl get deploy -o wide`.
3. Confirm database compatibility: application rollbacks must stay compatible
   with the schema the database currently has.
4. Never downgrade database schema automatically. For an incompatible
   migration, follow the migration-specific recovery procedure and restore
   only from a verified backup.
5. Re-run health, readiness and critical transaction smoke tests.
6. Record incident ID, versions, migration revision, operator and outcome.

## After the rollback
- Keep the failed build available for forensics; do not delete its images.
- Open a fix on a branch off the production commit (see
  `RELEASE_PROCESS.md`, hotfix path).
- Only re-promote through staging.
