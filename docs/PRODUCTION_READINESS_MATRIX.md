# ERP03 Production Readiness Matrix

This matrix records repository configuration and the latest observed evidence. A successful CI job is not production approval; live staging, rollback, backup/restore, secrets, TLS, and runtime verification remain separate gates.

| Area | Current evidence (2026-11-15) | State |
|---|---|---|
| Repository baseline | Main head: 716f305f27739c6f53dceac77126734795f2efa7 | OBSERVED |
| Code quality | Quality workflow run #401 on PR #271 head 1de6b8c: lint and format checks passed | PASS (PR head only) |
| CI | Run #745 on PR #271 head: backend compile, PostgreSQL migrations, pytest, frontend build and Docker publish contract tests passed | PASS (PR head only) |
| Security | Security workflow run #565 on PR #271 head: dependency audit and CodeQL jobs passed | PASS (PR head only) |
| Container | Frontend container workflow run #283 completed; PR event skipped registry login, publish and manifest verification | VALIDATION ONLY |
| Policy enforcement | Runs #43718798829 (#274), #43718901834 (#275), #43716474195 (#272), #43718634191 (#273), and #43711026050 (#271) ended startup_failure; zero jobs and no job logs | BLOCKED / UNRESOLVED |
| Infrastructure validation | Issue #268 records main run #43303393662 / check suite #117266055628 failing before job creation | BLOCKED / UNRESOLVED |
| Main branch ruleset | Active ruleset #26804940 requires one independent approval, latest-push approval, resolved threads, linear history and deployments to copilot + Docker01; required status-check list is empty; administrator role has always-bypass | CONFIGURED WITH GAPS |
| Staging deployment | .github/workflows/deploy-staging.yml deploys immutable GHCR digests over SSH + Docker Compose using environment staging; required-deployment names in main ruleset differ | NOT QUALIFIED |
| Backend publishing | .github/workflows/docker-publish.yml: GHCR, AMD64 + ARM64, SBOM, provenance, Cosign sign/verify configured | CONFIGURED; live publish evidence required |
| Frontend publishing | .github/workflows/container.yml: GHCR, AMD64 + ARM64, SBOM and provenance configured; no Cosign step observed | CONFIGURED; signing gap |
| Kubernetes image sources | Production and staging overlays still reference Docker Hub; production digest values remain placeholders | BLOCKED |
| Database protection | ERP03 Alembic migration chain exists in repository; connected Supabase erp03 project has no application tables or migration records | NOT CONNECTED / NOT QUALIFIED |
| Supabase security | rls_auto_enable() execution revoked from anon/authenticated/PUBLIC; ensure_rls event trigger preserved; security advisor returned no lints | VERIFIED for observed finding |
| Transaction integrity | Issue #222 remains open; journal acceptance is not proof of domain commit; domain-level idempotency/reconciliation acceptance criteria remain | BLOCKED |
| Performance qualification | No verified staging target or dedicated load-test suite was established; no staging benchmark was run | NOT RUN |
| Production readiness | No live staging, rollback, restore, end-to-end business-flow or production runtime evidence established in this inspection | NOT QUALIFIED |

## Immediate remediation priorities

1. Resolve the no-job Policy Enforcement and Infrastructure Validation startup failures through run/check-suite diagnostics. Do not convert them to success or weaken policy.
2. Correct the active main ruleset: explicitly require the intended stable CI/security/policy checks; align deployment environment names with the actual deployment workflow; review/remove the always-on administrator bypass unless a narrowly controlled emergency bypass is required.
3. Align Kubernetes image sources with the actual GHCR publishing workflows. Only populate deployment digests from successful trusted publication runs and verify both architectures.
4. Complete issue #222: domain-level idempotency in the same PostgreSQL transaction as business writes; bounded reconciliation with leases/claims; crash-window, duplicate-delivery and concurrent-worker tests.
5. Correct dependency/documentation drift. The checked-in frontend package manifest currently declares Vite 8.3.6 and plugin-react 6.2.1; older documentation and tracker entries mention incompatible older versions. Reconcile with the lockfile and successful builds before changing pins.
6. Qualify staging before load testing: verify the actual target, deployment path, credentials, immutable image digests, rollback baseline and a dedicated benchmark harness. Measure API latency/throughput/errors, DB pool/query behavior, Redis and frontend performance. Never load-test production or an unverified endpoint.

## Pull-request disposition

- PR #271: 2 changed files, 150 additions; head 1de6b8c90354e9f9f6a0c35fb35181733613341b. CI, Quality, Security and Container jobs passed, including the Docker publishing contract tests. Policy Enforcement still fails before creating jobs. No review approvals or review threads were recorded. Do not merge until the independent approval and configured deployment/status gates are satisfied.
- PR #272: documentation-only readiness refresh; normal CI, Quality, Security, Container, Type Check, Coverage, Docker and Agent Parity runs passed on its head. Policy Enforcement remains a zero-job startup failure. Independent review is outstanding.
- PR #273: Myanmar-aware operations theme is implemented in frontend source (Layout.jsx, styles.css, tailwind.config.js); normal CI, Quality, Security, Container, Type Check, Coverage, Docker, Agent Parity and Devcontainer checks passed. Browser/accessibility verification remains outstanding; this is not a complete translation or accessibility certification.
- PR #274: JWT signature/expiry verification now guards tenant rate-limit bucket selection; regression tests cover valid, forged and expired tokens. CI, Quality, Type Check, Coverage, Container, Docker, Security, Agent Parity and Devcontainer checks passed. CodeQL is neutral because two prior configurations were not found; Supabase Preview was skipped. PR is ready for review, but independent approval and policy/deployment gates are outstanding.
- PR #275: per-process DB pool cap is 4 pooled + 2 overflow; checked-in production HPA max is 10 replicas and backend Dockerfile starts one Uvicorn process, yielding an API-side upper bound of 60 connections. Regression tests cover production, staging and development. The same normal CI suites passed; CodeQL is neutral and Supabase Preview skipped. PR is ready for review, but independent approval and policy/deployment gates are outstanding.
- PR #270: 51,884 changed files, 5,204,634 additions and 660 deletions; currently non-mergeable. Do not merge; reconstruct only intended changes from current main in a bounded PR.

## Supabase project boundary

The connected Supabase project ref gtnhalgelambuzajwuqi is healthy but has zero public application tables and no migration history. It is not demonstrated to be the ERP03 runtime database. Keep the backend's configured PostgreSQL/Alembic data path authoritative unless a documented integration decision changes that architecture. Do not create parallel ERP schema here.

## Evidence rules

- Distinguish repository configuration from executed runtime evidence.
- A skipped publish step on a pull-request event is not a successful registry publication.
- A migration file existing in Git is not proof it was applied to production.
- A journal row or accepted operation is not proof that invoice, payment or stock mutation committed.
- Never use placeholder digests in a production deployment.
