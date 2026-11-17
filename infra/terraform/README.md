# ERP03 Infrastructure as Code

This directory defines the provider-neutral Terraform/OpenTofu boundary for ERP03.

Required environment separation:
- dev
- staging
- production

Provider, region, network CIDRs, managed database identifiers, and state backend are deployment-specific and must be supplied by the operator. No credentials or provider assumptions belong in this repository.

Before apply:
1. `terraform fmt -check -recursive`
2. `terraform init`
3. `terraform validate`
4. `terraform plan`
5. Review the plan and obtain approval.
6. Apply only the approved plan.
