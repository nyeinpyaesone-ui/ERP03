# ERPNext Production Profile

This directory is an isolated ERPNext/Frappe production profile inside the `feat/erpnext-production` branch of ERP03.

It does **not** replace the existing ERP03 application. `main` remains the existing ERP03 system.

## Production target

- ERPNext: v16.31.1
- Frappe branch: `version-16`
- Container source: official `frappe/frappe_docker`
- Image registry: GHCR
- Image identity: commit SHA + pinned ERPNext release tag
- Deployment model: official Frappe Docker production Compose architecture
- Client target: UAT before August 29, 2026 production go-live

## Why this differs from the original proposal

The initial proposal used a hand-written `frappe/erpnext` Dockerfile and a Kubernetes `bench migrate` Job. The official Frappe Docker project now provides the supported production Compose architecture, custom/layered image builds, and a dedicated migrator service. We therefore reuse the upstream production machinery rather than duplicating it in ERP03.

For real production/custom-app CI, the official guidance recommends the `custom` or `layered` image paths rather than the basic production image. Custom app definitions are supplied through `apps.json`; BuildKit secrets must be used instead of Docker build arguments for private app credentials.

## Build flow

```text
ERP03 branch
    |
    +-- infra/erpnext/apps.json
    |
    v
GitHub Actions
    |
    +-- checkout official frappe_docker
    +-- BuildKit layered image
    +-- SBOM / provenance
    +-- Trivy HIGH/CRITICAL scan
    |
    v
GHCR
    |
    +-- <commit SHA>   immutable deployment candidate
    +-- v16.31.1       release reference
    |
    v
UAT deployment
    |
    +-- create/verify site
    +-- install ERPNext
    +-- smoke test
    +-- business UAT
    |
    v
Production approval
```

## Deployment rule

Do not deploy `latest` to production. Use the immutable Git commit tag or image digest produced by CI.

Do not store production passwords, API keys, certificates, or tokens in this repository.

## UAT minimum gate

Before production approval, verify:

1. Site opens over HTTPS.
2. Administrator login works.
3. Company and fiscal-year configuration is correct.
4. Customer and supplier creation works.
5. Item, warehouse, and stock transactions work.
6. Sales and purchase flows work.
7. Accounting posting and reports work.
8. Background jobs and scheduler are healthy.
9. File upload/download works.
10. Database backup and restore have been tested.
11. Production image is the exact image tested in UAT.

## Migration safety

ERPNext database migrations are stateful. A failed application rollout does not automatically undo database changes. Take a verified backup before production migration and only promote an image that has passed UAT.

## Upstream reference

Official deployment source: https://github.com/frappe/frappe_docker

Use the upstream `compose.yaml` and appropriate production overrides. Do not copy the disposable `pwd.yml` setup into production.
