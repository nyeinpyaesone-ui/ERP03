# ERP03 Deployment Runbook

## Preconditions
1. CI, Quality, Security, Container, and Qualification checks are green.
2. Exact commit SHA and image digests are recorded.
3. Database backup completed successfully.
4. Staging smoke verification is approved.

## Deployment
1. Promote the immutable build for the approved commit.
2. Apply migrations before application rollout.
3. Roll out backend and frontend workloads.
4. Verify `/api/v1/healthz`, `/api/v1/readyz`, and `/metrics`.
5. Verify authentication, sales, and transaction critical paths.
6. Monitor error rate, latency, saturation, and database health.

## Stop conditions
- Migration failure.
- Readiness failure.
- Elevated 5xx responses.
- Security gate failure.
- Unexpected transaction behavior.

## Evidence
Record commit SHA, image digest, migration revision, deployment time, operator, and smoke-test result.
