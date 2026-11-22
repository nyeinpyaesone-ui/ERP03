#!/usr/bin/env bash
set -Eeuo pipefail

# ERP03 Kubernetes production deployment is deliberately blocked.
#
# The previous implementation did not apply the supplied application digest,
# accepted a single digest for two independently published images, skipped
# cluster verification when kubectl was absent, and contained placeholder
# image/health checks. Keeping a partially functional production deploy script
# is more dangerous than failing closed.
#
# Do not replace this guard with a deploy implementation until the production
# release gates in issues #222, #268, #286, and #287 have reproducible evidence.

cat >&2 <<'MESSAGE'
ERROR: ERP03 Kubernetes production deployment is disabled.

No cluster connection, manifest apply, migration, or workload change was made.

Blocking conditions that must be closed before implementing/enabling this path:
  - Shared PostgreSQL-backed transaction journal and crash/concurrency recovery
    tests are not complete (#222; PR #294 is only a fail-closed guard).
  - Policy Enforcement / Infrastructure Validation startup failures have no
    actionable pre-job diagnostics yet (#268). A zero-job startup_failure is
    not a passing required check.
  - Production release controls, immutable image qualification, database
    recovery, and staging acceptance remain open (#286, #287).
  - The current production Kubernetes overlay still contains unresolved
    application image digest placeholders on this baseline.
  - The production PostgreSQL and Redis topology has not demonstrated HA,
    backup restoration, or failover recovery.

The open PR #296 describes a separate single-host Docker Compose production
workflow; it is not a qualified Kubernetes deployment and must not be treated
as proof of Kubernetes HA or zero downtime.

After every gate is closed, implement and independently validate a new
Kubernetes deployment contract with separate backend/frontend digests,
signature and source-revision verification, exact cluster identity, rendered
manifest validation, controlled migration, health checks, and rollback.

See:
  https://github.com/nyeinpyaesone-ui/ERP03/issues/222
  https://github.com/nyeinpyaesone-ui/ERP03/issues/268
  https://github.com/nyeinpyaesone-ui/ERP03/issues/286
  https://github.com/nyeinpyaesone-ui/ERP03/issues/287
MESSAGE

exit 78
