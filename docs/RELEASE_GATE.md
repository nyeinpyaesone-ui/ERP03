# Release Gate

## Pre-release checks
- [ ] CI workflows green: quality, security, container, iac
- [ ] Terraform plan artifact uploaded and reviewed
- [ ] Backup verification script succeeds in staging
- [ ] Prometheus alerts configured
- [ ] Devcontainer builds successfully

## Approval
- [ ] Code owner review
- [ ] Production readiness matrix updated to PASS
- [ ] Secrets rotated if changed

## Post-release
- [ ] Health checks pass
- [ ] Metrics dashboards updated
- [ ] Runbook updated if changes affect ops
