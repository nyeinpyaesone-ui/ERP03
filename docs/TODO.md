# ERP03 Remediation Tracker

**Updated:** 2026-11-15 · **Source:** live GitHub PR/workflow inspection + connected Supabase security review.
**Method:** branch from current main, reproduce with evidence, make one minimal change per PR, run mandatory tests, record commit SHA and output. Never equate a green source-level check with production qualification.

Severity: **P0** startup/contract or critical security · **P1** transaction correctness/security · **P2** documentation, operational evidence and UX.

## P0 — open

- [ ] **CI-STARTUP-1: Policy Enforcement startup failure.** PR head `1de6b8c90354e9f9f6a0c35fb35181733613341b` run `43711026050` ended `startup_failure`; zero jobs and no job logs. Obtain run/check-suite admission diagnostics; do not weaken policies.
- [ ] **IAC-STARTUP-1: Infrastructure Validation startup failure.** Main issue #268 documents run `43303393662` and check suite `117266055628`, zero jobs. Confirm whether GitHub Actions registration/admission or repository configuration is responsible, then run and verify.
- [ ] **DEPLOY-REGISTRY-1: Kubernetes registry mismatch.** Backend/frontend publishing uses GHCR, but production/staging Kustomize overlays still target Docker Hub; production digest fields are placeholders. Align source image names after verifying actual GHCR publication, then pin the immutable published digests. Never deploy placeholder digests.

## P1 — open

- [ ] **TX-1: Durable cross-module transaction integrity (issue #222).** Implement the operation state machine and domain-level idempotency in the same PostgreSQL transaction as invoice/payment/stock writes. Add leases/claims, bounded retries, reconciliation/manual-review states, duplicate delivery and crash-window tests, structured observability and a recovery runbook. A journal acceptance record is not evidence of a committed business mutation.
- [ ] **DB-BOUNDARY-1: Supabase runtime integration decision.** Connected project `erp03` (ref `gtnhalgelambuzajwuqi`) is healthy but has zero public application tables and no migration history. Do not dual-write or create parallel ERP tables until the production PostgreSQL authority and intended Supabase role (if any) are explicitly documented.
- [ ] **FRONTEND-DEPS-1: Reconcile manifest/lockfile/docs.** Checked `frontend/package.json` declares Vite 8.3.6 and `@vitejs/plugin-react` 6.2.1, while historical docs/tracker refer to older Vite lines. Verify package-lock consistency and actual successful build before changing any version.
- [ ] **FRONTEND-UI-1: Implement Myanmar-aware design tokens in the real frontend.** Current Themely preview is a design artifact only; no source integration or accessibility test has been committed.

## P2 — staging / production evidence

- [ ] Validate Prometheus rules with `promtool check rules` and load them in staging Prometheus.
- [ ] Run trusted multi-architecture container builds and Trivy scanning; collect build digests and SBOM/provenance artifacts. PR-event container runs skip registry login and publication, so they do not prove published images.
- [ ] Execute PostgreSQL backup and restore into a scratch database; verify Alembic head and application-level integrity.
- [ ] Complete staging smoke/E2E tests, payment/inventory reconciliation, rollback verification, secret rotation, TLS and monitoring alert tests.
- [ ] Replace outdated production qualification assertions with exact run URLs, commit SHAs, image digests, test evidence and environment references.

## Verified work — 2026-11-15

- Supabase migration `20261115125601` / `restrict_rls_auto_enable_rpc_execution` applied. Revoked `EXECUTE` on `public.rls_auto_enable()` from `anon`, `authenticated`, and `PUBLIC`; retained `service_role`. Verified the `ensure_rls` event trigger remains enabled and attached. Security advisor returned no lints. This change does not create ERP schema or modify business data.
- PR #271 current head `1de6b8c90354e9f9f6a0c35fb35181733613341b`: CI run #745, Quality #401, Security #565 and Container #283 completed successfully; Policy Enforcement #236 failed before job creation. No PR reviews or review threads were recorded. Merge remains gated.
- PR #270 remains unsuitable: 51,884 changed files, 5,204,634 additions, and currently non-mergeable. Do not merge; reconstruct only intended source changes from current main.

## Completion evidence format

For each closed item record: PR URL, branch/head SHA, test commands and results, database migration/version if applicable, workflow run URLs, staging environment, image digests/SBOM/signature verification and rollback evidence. Keep production status **NOT QUALIFIED** until all required runtime gates have reproducible evidence.
