# ERP03 Infrastructure

## Current state

Kubernetes manifests are present in the repository, but infrastructure provisioning is not yet codified with Terraform/OpenTofu.

Do not apply production manifests directly from this repository until image references, secrets, storage, ingress/TLS, resource limits, probes, backup/restore, and rollback have passed staging validation.

## Execution order

1. Build and validate immutable application images.
2. Deploy the same image digests to staging.
3. Validate health, migrations, smoke tests, logs, metrics, and rollback.
4. Provision production infrastructure through reviewed IaC.
5. Apply Kubernetes manifests through the release pipeline.
6. Promote only the validated image digests.

## Terraform/OpenTofu

Reserved structure:

```text
infra/
  terraform/
    modules/
    environments/
      dev/
      staging/
      production/
```

This structure is intentionally not populated with provider-specific resources until the target hosting environment is confirmed. Inventing cloud resources here would create an inaccurate production plan.
