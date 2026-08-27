# ERPNext Production — Unfinished / Unsuccessful Task Matrix

Branch: `feat/erpnext-production`
Target: client UAT before 2026-08-29 production go-live.

This file is the authoritative implementation checklist for the ERPNext production profile. `main` is out of scope and must remain unchanged.

## Current verified state

- [x] Dedicated branch exists: `feat/erpnext-production`.
- [x] ERPNext release is pinned to `v16.31.1`.
- [x] Frappe branch is pinned to `version-16`.
- [x] Official `frappe/frappe_docker` layered-image path is selected.
- [x] GHCR image naming is defined.
- [x] Build workflow exists.
- [x] `apps.json` exists and currently references the official ERPNext v16 app.
- [ ] Production deployment manifests are not yet present.
- [ ] ArgoCD Application is not yet present.
- [ ] External Secrets resources are not yet present.
- [ ] Prometheus/Grafana monitoring resources are not yet present.
- [ ] CI has not yet been verified by a successful GitHub Actions run.
- [ ] GHCR image publication has not yet been verified from this branch.
- [ ] UAT environment has not been verified.
- [ ] Client UAT has not been completed.
- [ ] Production infrastructure has not been verified.

## P0 — Must complete before client UAT

### 1. Custom image build correctness

- [ ] Pin the upstream `frappe_docker` checkout to a reviewed commit/tag instead of an unqualified moving default branch.
- [ ] Verify the layered `Containerfile` accepts the supplied `apps_json` BuildKit secret.
- [ ] Verify `apps.json` contains only intended apps and pinned branches/refs.
- [ ] Add a deterministic build validation step that fails on missing app metadata or dependency resolution errors.
- [ ] Ensure no production secret is passed through Docker `ARG`, image labels, workflow logs, or committed files.
- [ ] Verify the resulting image contains ERPNext and all declared custom apps.
- [ ] Verify the image starts successfully with the official Frappe production command set.

### 2. CI quality gates

- [ ] Add lint/static validation for YAML, JSON and Kubernetes manifests.
- [ ] Add configuration/schema validation for `apps.json`.
- [ ] Build on pull requests and the release branch; production publication must remain restricted to the intended release path.
- [ ] Authenticate to GHCR using `GITHUB_TOKEN` with only `packages:write` and required security permissions.
- [ ] Publish an immutable commit-SHA tag.
- [ ] Prefer deployment by image digest after publication; never deploy `latest`.
- [ ] Generate SBOM and provenance and retain the build metadata.
- [ ] Run Trivy against the exact immutable image.
- [ ] Make the vulnerability policy explicit: HIGH/CRITICAL findings must fail the release unless a documented, reviewed exception exists.
- [ ] Upload SARIF only after the scan step completes successfully.
- [ ] Verify a real workflow run from this branch and record the resulting image digest.

### 3. Production runtime configuration

- [ ] Add the official Frappe Docker production Compose files/overrides required by the selected deployment model.
- [ ] Define site creation/bootstrap configuration separately from runtime configuration.
- [ ] Define database host/user/password configuration using deployment secrets, not repository values.
- [ ] Define Redis cache and queue endpoints according to the official Frappe Docker service names.
- [ ] Define socket/realtime and worker/scheduler services required by ERPNext.
- [ ] Configure persistent volumes for sites/private files/public files and database data where applicable.
- [ ] Configure HTTPS/TLS and canonical site hostname.
- [ ] Configure upload/body-size and request timeout limits appropriate for ERP attachments.
- [ ] Verify timezone, locale and site configuration for the client's operating requirements.

### 4. Kubernetes/GitOps path from the supplied specification

- [ ] Add `gitops/deployment.yaml` with a real immutable ERPNext image reference.
- [ ] Add `gitops/service.yaml`.
- [ ] Add `gitops/ingress.yaml` with TLS and the real client hostname supplied at deployment time.
- [ ] Add `gitops/migrate-job.yaml` with a unique release-specific Job name or hook strategy; do not reuse a completed Job name across releases.
- [ ] Add `gitops/kustomization.yaml` and environment overlays.
- [ ] Do not rely on `${IMAGE_TAG}` magically being substituted; implement an explicit GitOps image-update mechanism.
- [ ] Configure rolling-update parameters and readiness gates appropriate to ERPNext startup time.
- [ ] Do not claim database rollback from Kubernetes pod rollback. Database backup/restore is the recovery mechanism for failed migrations.
- [ ] Define migration ordering explicitly and verify it against the selected Frappe Docker production architecture.

### 5. Secrets

- [ ] Add `ExternalSecret` only after a real `ClusterSecretStore`/`SecretStore` exists.
- [ ] Define the exact secret keys required by the selected Frappe Docker deployment.
- [ ] Keep Vault/KMS paths environment-specific.
- [ ] Verify secret refresh and pod consumption without exposing values in logs.
- [ ] Remove placeholder production credentials from any deployment-ready configuration.

## P1 — Required for production certification

### 6. Health and observability

- [ ] Define a Frappe-compatible readiness check that proves the site is usable, not merely that TCP port 8000 is open.
- [ ] Define liveness behavior that will not restart healthy but slow-starting workers.
- [ ] Add metrics collection using the monitoring mechanism actually supported by the deployed Frappe version; do not assume a Django-specific `/metrics` endpoint exists.
- [ ] Add PostgreSQL/MariaDB monitoring appropriate to the actual database selected by the deployment.
- [ ] Add Redis queue/cache monitoring.
- [ ] Add alerts for application errors, queue backlog, failed jobs, database availability and restart loops.

### 7. Backup and recovery

- [ ] Define scheduled database backups.
- [ ] Back up ERPNext site files/private files as required.
- [ ] Store backups outside the application container host.
- [ ] Perform a real restore test before production approval.
- [ ] Record backup retention and recovery owner.
- [ ] Take a verified pre-migration backup before every production schema migration.

### 8. Security hardening

- [ ] Replace all placeholder hostnames, email addresses and credentials before deployment.
- [ ] Verify TLS certificate issuance/renewal.
- [ ] Restrict ingress to required hosts/ports.
- [ ] Apply non-root/container security controls only where compatible with the official Frappe image/runtime.
- [ ] Verify image provenance/SBOM availability.
- [ ] Verify no secrets are present in Git history for this branch.

## P1 — Client UAT acceptance gate

- [ ] HTTPS site opens from the client network.
- [ ] Administrator login succeeds.
- [ ] Company and fiscal-year configuration is correct.
- [ ] Users, roles and permissions are correct.
- [ ] Customer creation and retrieval works.
- [ ] Supplier creation and retrieval works.
- [ ] Item creation and stock settings work.
- [ ] Warehouse setup works.
- [ ] Purchase transaction posts correctly.
- [ ] Sales transaction posts correctly.
- [ ] Stock movement/ledger is correct.
- [ ] Accounting entries and balances are correct.
- [ ] Required reports render and export.
- [ ] Background jobs/scheduler are healthy.
- [ ] File upload/download works.
- [ ] Backup and restore test passes.
- [ ] The exact image digest tested in UAT is promoted to production.

## P2 — Enterprise hardening after first successful go-live

- [ ] Separate dev/staging/production overlays.
- [ ] Automated image promotion from UAT-approved digest to production.
- [ ] ArgoCD sync policy and project restrictions.
- [ ] Deployment notifications/audit trail.
- [ ] Disaster-recovery exercise.
- [ ] Capacity/load testing.
- [ ] HA database/Redis strategy if required by SLA.

## Explicit unsuccessful/invalid patterns to avoid

- [ ] Do not use `latest` for production deployment.
- [ ] Do not assume `${IMAGE_TAG}` is automatically substituted by ArgoCD/Kustomize.
- [ ] Do not use a Kubernetes Job named identically for every migration release without a hook/name strategy.
- [ ] Do not claim automatic database rollback from Deployment rollback.
- [ ] Do not use `bench get-app` against an app that has already been supplied by the custom image unless the selected Frappe Docker build process specifically requires it.
- [ ] Do not use `pip install ... || true` for production dependency installation; dependency failure must fail the image build.
- [ ] Do not invent a Django/Prometheus endpoint for Frappe without verifying it exists in the deployed version.
- [ ] Do not deploy until the exact client UAT image digest has been verified.

## Release gate

Production status is **NO-GO** until every P0 item and every client UAT acceptance item required for the client's scope is checked and independently verified.
