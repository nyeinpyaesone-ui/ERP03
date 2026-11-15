# ERP03 Production Readiness Matrix

This matrix records repository configuration and the latest observed evidence. A successful CI job is not production approval; live staging, rollback, backup/restore, secrets, TLS, and runtime verification remain separate gates.

| Area | Current evidence (2026-11-15) | State |
|---|---|---|
| Repository baseline | Main head at last inspection: `716f305f27739c6f53dceac77126734795f2efa7` | OBSERVED |
| Code quality | Quality workflow run #401 on PR head `1de6b8c`: lint and format checks passed | PASS (PR head only) |
| CI | Run #745 on PR head: backend compile, PostgreSQL migrations, pytest, frontend build and Docker publish contract tests passed | PASS (PR head only) |
| Security | Security workflow run #565 on PR head: dependency audit and CodeQL jobs passed | PASS (PR head only) |
| Container | Frontend container workflow run #283 completed; PR event skipped registry login, publish and manifest verification | VALIDATION ONLY |
| Policy enforcement | Run #236 on PR head ended `startup_failure`; zero jobs created, no job logs | BLOCKED |
| Infrastructure validation | Main-branch issue #268 records earlier `startup_failure` / zero-job runs; investigate run-level admission diagnostics | BLOCKED / UNRESOLVED |
| Backend publishing | `.github/workflows/docker-publish.yml`: GHCR, AMD64 + ARM64, SBOM, provenance, Cosign sign/verify configured | CONFIGURED; live publish evidence required |
| Frontend publishing | `.github/workflows/container.yml`: GHCR, AMD64 + ARM64, SBOM and provenance configured; no Cosign step observed | CONFIGURED; signing gap |
| Kubernetes image sources | Production and staging overlays still reference Docker Hub; production digest values remain placeholders | BLOCKED |
| Database protection | ERP03 Alembic migration chain exists in repository; connected Supabase `erp03` project has no application tables or migration records | NOT CONNECTED / NOT QUALIFIED |
| Supabase security | `rls_auto_enable()` execution revoked from anon/authenticated/PUBLIC; `ensure_rls` event trigger preserved; security advisor returned no lints | VERIFIED for observed finding |
| Transaction integrity | Issue #222 remains open; journal acceptance is not proof of domain commit; domain-level idempotency/reconciliation acceptance criteria remain | BLOCKED |
| Production readiness | No live staging, rollback, restore, end-to-end business-flow or production runtime evidence established in this inspection | NOT QUALIFIED |

## Immediate remediation priorities

1. Resolve the no-job Policy Enforcement and Infrastructure Validation startup failures without converting them to success or weakening policies.
2. Align Kubernetes image sources with the actual GHCR publishing workflows. Only populate deployment digests from successful trusted publication runs and verify both architectures.
3. Complete issue #222: domain-level idempotency in the same PostgreSQL transaction as business writes; bounded reconciliation with leases/claims; crash-window, duplicate-delivery and concurrent-worker tests.
4. Correct dependency/documentation drift. The checked-in frontend package manifest currently declares Vite 8.3.6 and plugin-react 6.2.1; older documentation and tracker entries mention incompatible older versions. Reconcile with the lockfile and successful builds before changing pins.
5. Execute staging restore, monitoring-rule validation, container scanning, backup/restore and rollback drills. Record run IDs, image digests, database migration head and operator evidence.

## Pull-request disposition

- PR #271: 2 changed files, 150 additions; current head `1de6b8c90354e9f9f6a0c35fb35181733613341b`. CI, Quality, Security and Container workflow runs observed successful on the PR head, but Policy Enforcement is a zero-job startup failure. No reviews or review threads were recorded at inspection. Do not merge until the required policy/startup check is resolved and the full required-check set is green.
- PR #270: 51,884 changed files, 5,204,634 additions, 660 deletions; currently non-mergeable. Do not merge; reconstruct only intended changes from current main in a bounded PR.

## Supabase project boundary

The connected Supabase project ref `gtnhalgelambuzajwuqi` is healthy but has zero public application tables and no migration history. It is not demonstrated to be the ERP03 runtime database. Keep the backend's configured PostgreSQL/Alembic data path authoritative unless a documented integration decision changes that architecture. Do not create parallel ERP schema here.

## Evidence rules

- Distinguish repository configuration from executed runtime evidence.
- A skipped publish step on a pull-request event is not a successful registry publication.
- A migration file existing in Git is not proof it was applied to production.
- A journal row or accepted operation is not proof that invoice, payment or stock mutation committed.
- Never use placeholder digests in a production deployment.
