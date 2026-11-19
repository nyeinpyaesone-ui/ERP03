# ERP03 Remediation Tracker

**Updated:** 2026-11-15 · **Source:** live GitHub PR/workflow and active ruleset inspection + connected Supabase security review.
**Method:** branch from current main, reproduce with evidence, make one minimal change per PR, run mandatory tests, record commit SHA and output. Never equate a green source-level check with production qualification.

Severity: **P0** startup/merge-control/critical security · **P1** transaction correctness/security · **P2** documentation, operational evidence and UX.

## P0 — open

- [ ] **CI-STARTUP-1: Policy Enforcement startup failure.** Runs #43718798829 (#274), #43718901834 (#275), #43716474195 (#272), #43718634191 (#273), and #43711026050 (#271) ended startup_failure with zero jobs. Timing records have no billable job data and there are no job logs. Obtain GitHub check-suite/workflow admission diagnostics; do not weaken policy or treat a rerun as a fix without job creation and successful validation.
- [ ] **IAC-STARTUP-1: Infrastructure Validation startup failure.** Main issue #268 documents run #43303393662 and check suite #117266055628, zero jobs. Obtain run/check-suite diagnostics and verify the workflow creates jobs and passes.
- [ ] **RULESET-1: Repair main branch merge controls.** Active ruleset #26804940 has an empty required_status_checks array, requires deployments to exact environment names copilot and Docker01, and has an always-bypass actor for the repository administrator. Define stable required CI/security/policy check names, align deployment names with real workflows/environments, and remove or narrowly constrain routine bypass. Do not bypass during remediation.
- [ ] **DEPLOY-REGISTRY-1: Kubernetes registry mismatch.** Backend/frontend publishing uses GHCR, but production/staging Kustomize overlays still target Docker Hub; production digest fields are placeholders. Align source image names only after verifying actual trusted GHCR publications, then pin immutable digests. Never deploy placeholder digests.
- [ ] **STAGING-ENV-1: Deployment environment alignment.** deploy-staging.yml uses environment staging and SSH + Docker Compose with immutable GHCR digests. The main ruleset requires copilot and Docker01; a previously inspected environment named Docker1 is not the same as Docker01. Verify exact environments and successful deployment records before changing the ruleset or workflow.

## P1 — open

- [ ] **TX-1: Durable cross-module transaction integrity (issue #222).** Implement the operation state machine and domain-level idempotency in the same PostgreSQL transaction as invoice/payment/stock writes. Add leases/claims, bounded retries, reconciliation/manual-review states, duplicate delivery and crash-window tests, structured observability and a recovery runbook. A journal acceptance record is not evidence of a committed business mutation.
- [ ] **DB-BOUNDARY-1: Supabase runtime integration decision.** Connected project erp03 (ref gtnhalgelambuzajwuqi) is healthy but has zero public application tables and no migration history. Do not dual-write or create parallel ERP tables until the production PostgreSQL authority and intended Supabase role (if any) are explicitly documented.
- [ ] **FRONTEND-DEPS-1: Reconcile manifest/lockfile/docs.** Checked frontend/package.json declares Vite 8.3.6 and @vitejs/plugin-react 6.2.1, while historical docs/tracker refer to older Vite lines. Verify package-lock consistency and actual successful build before changing any version.
- [ ] **FRONTEND-UI-1: Complete Myanmar-aware operations UI validation.** PR #273 now contains actual source changes in Layout.jsx, styles.css and tailwind.config.js. It remains draft; browser-level keyboard/focus/contrast testing and page-level Burmese translation review are still outstanding. The implementation is not yet merged or accessibility-certified.

## P2 — staging / production evidence

- [ ] Validate Prometheus rules with promtool check rules and load them in staging Prometheus.
- [ ] Run trusted multi-architecture container builds and Trivy scanning; collect build digests and SBOM/provenance artifacts. PR-event container runs skip registry login and publication, so they do not prove published images.
- [ ] Execute PostgreSQL backup and restore into a scratch database; verify Alembic head and application-level integrity.
- [ ] Complete staging smoke/E2E tests, payment/inventory reconciliation, rollback verification, secret rotation, TLS and monitoring alert tests.
- [ ] Establish a dedicated load-test harness and safe staging target. Do not benchmark until immutable image digests, deployment path, credentials, rollback baseline and staging health checks are verified. No benchmark was run in this inspection.
- [ ] Replace outdated production qualification assertions with exact run URLs, commit SHAs, image digests, test evidence and environment references.

## Verified work — 2026-11-15

- Supabase migration 20261115125601 / restrict_rls_auto_enable_rpc_execution applied. Revoked EXECUTE on public.rls_auto_enable() from anon, authenticated and PUBLIC; retained service_role. Verified the ensure_rls event trigger remains enabled and attached. Security advisor returned no lints. This change does not create ERP schema or modify business data.
- PR #271 current head 1de6b8c90354e9f9f6a0c35fb35181733613341b: CI run #745, Quality #401, Security #565 and Container #283 completed successfully. The new docker-publish-contract job passed; it tests the canonical GHCR publisher without performing a publish. Policy Enforcement #43711026050 failed before job creation. No independent PR review was recorded.
- PR #274 current head 1afef51038a7acc4f254e2f25fde7625eb623f8f: 15 successful checks; CodeQL neutral (two prior configurations not found); Supabase Preview skipped; Policy Enforcement #43718798829 startup_failure/zero jobs. Marked ready for review; no independent approval.
- PR #275 current head 11cfee7f3a4fd816242811b42cfc95e05971f205: 15 successful checks; CodeQL neutral; Supabase Preview skipped; Policy Enforcement #43718901834 startup_failure/zero jobs. Marked ready for review; no independent approval. Backend pool cap is 4 pooled + 2 overflow per process; HPA max is 10 API pods and Dockerfile starts one Uvicorn process, yielding an API-side upper bound of 60 connections.
- PR #272 documentation refresh and PR #273 UI source changes have successful normal CI/security/container/type/coverage checks, but Policy Enforcement remains startup-failing and both need independent review; #273 still needs browser/accessibility verification.
- PR #270 remains unsuitable: 51,884 changed files, 5,204,634 additions and currently non-mergeable. Do not merge; reconstruct only intended source changes from current main.

## Completion evidence format

For each closed item record: PR URL, branch/head SHA, test commands and results, database migration/version if applicable, workflow run URLs, staging environment, image digests/SBOM/signature verification and rollback evidence. Keep production status NOT QUALIFIED until all required runtime gates have reproducible evidence.
