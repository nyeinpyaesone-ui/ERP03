# ERP03 Deployment Runbook

## Preconditions
1. CI, Quality, Security, Container and Qualification checks are green for the
   exact commit (`gh run list --commit <sha>`).
2. Image digests exist in GHCR for that commit (`Container` pushes them on
   `main`; any branch can be pushed on demand with the `Container Push`
   workflow or, locally, `make container-push`).
3. Database backup completed and its checksum verified (`scripts/backup.sh`).
4. Staging deployment of the same commit is live and smoke-tested.
5. Staging sign-off recorded before any production promotion.

## Staging
Triggered automatically on `main`, or manually with a chosen image tag:

```bash
gh workflow run deploy-staging.yml -f image_tag=<commit-sha>
```

The workflow resolves immutable digests, pins them into
`infra/kubernetes/overlays/staging`, runs `alembic upgrade head` in a
short-lived pod, applies the overlay, waits for rollout and runs smoke checks.
Review its step summary for the promoted digests.

## Production
Manual only, gated by the protected `production` environment:

```bash
gh workflow run deploy-production.yml \
  -f image_tag=<staging-validated-sha> \
  -f migration_note="<change link / reason>"
```

Order of operations inside the workflow:
1. Verify the candidate's gates passed.
2. Verify the currently running release is healthy (refuse to deploy blind).
3. Run migrations.
4. Apply the production overlay with pinned digests.
5. Wait for rollout, then smoke test.

## Manual verification after any deployment
```bash
BASE_URL=https://erp.example.invalid API_TOKEN=... scripts/smoke.sh
```
- `GET /api/v1/healthz` — liveness
- `GET /api/v1/readyz` — database reachable and schema migrated
- `GET /metrics` — Prometheus exposition present
- Authentication, sales and transaction critical paths
- Error rate, latency, saturation and database health in Grafana

## Stop conditions
- Migration failure.
- Readiness failure or failing smoke checks.
- Elevated 5xx responses.
- Security gate failure.
- Unexpected transaction behaviour.

## Evidence
Record commit SHA, image digests, migration revision, deployment time,
operator and smoke-test result. The deploy workflow writes all of these to its
step summary; copy them into the release notes.
