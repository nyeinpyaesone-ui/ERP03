# Getting Started with Terraform

This guide will help you provision the ERP infrastructure using Terraform.

## Prerequisites

1. **Terraform** >= 1.5.0 installed
2. **AWS CLI** configured with appropriate credentials
3. **kubectl** for interacting with EKS (optional, for later steps)

## Quick Start

### 1. Initialize Terraform

```bash
cd infra/terraform
terraform init
```

### 2. Configure Environment Variables

Copy the example variables file and customize:

```bash
# For Development
cp environments/dev.tfvars.example environments/dev.tfvars
nano environments/dev.tfvars  # Edit with your values

# For Staging
cp environments/staging.tfvars.example environments/staging.tfvars

# For Production
cp environments/production.tfvars.example environments/production.tfvars
```

**Important**: Never commit `*.tfvars` files to version control!

### 3. Plan Infrastructure

```bash
# Development
terraform plan -var-file=environments/dev.tfvars

# Staging
terraform plan -var-file=environments/staging.tfvars

# Production
terraform plan -var-file=environments/production.tfvars
```

### 4. Apply Infrastructure

```bash
# Development
terraform apply -var-file=environments/dev.tfvars

# Staging
terraform apply -var-file=environments/staging.tfvars

# Production (with confirmation)
terraform apply -var-file=environments/production.tfvars -auto-approve=false
```

### 5. Review Outputs

After successful application, Terraform will output important information:

```
Outputs:

vpc_id = "vpc-xxxxx"
private_subnet_ids = ["subnet-xxx", "subnet-yyy", "subnet-zzz"]
rds_endpoint = "prod-erp-db.xxx.us-east-1.rds.amazonaws.com:5432"
redis_primary_endpoint = "prod-erp-redis.xxx.cache.amazonaws.com:6379"
backup_bucket = "prod-erp-backups-xxxx"
```

## Environment Differences

| Feature | Development | Staging | Production |
|---------|-------------|---------|------------|
| VPC CIDR | 10.0.0.0/16 | 10.1.0.0/16 | 10.2.0.0/16 |
| RDS Instance | db.t3.medium | db.r6g.large | db.r6g.xlarge |
| Multi-AZ | No | Yes | Yes |
| Redis Nodes | 2 | 3 | 6 |
| NAT Gateways | 1 (shared) | 3 | 3 |
| S3 Backup Retention | 30 days | 30 days | 90 days + Glacier |

## Security Best Practices

### Managing Secrets

**DO NOT** store secrets in `.tfvars` files for production. Instead:

1. **Use AWS Secrets Manager**:
   ```hcl
   data "aws_secretsmanager_secret_version" "db_password" {
     secret_id = "erp/prod/db-password"
   }
   
   password = data "aws_secretsmanager_secret_version".db_password.secret_string
   ```

2. **Use Environment Variables**:
   ```bash
   export TF_VAR_db_password=$(aws secretsmanager get-secret-value ...)
   terraform apply -var-file=environments/production.tfvars
   ```

3. **Use CI/CD Pipeline Secrets**: Store secrets in GitHub Actions, GitLab CI, or similar.

### State Management

For production, configure remote state storage:

```hcl
terraform {
  backend "s3" {
    bucket         = "erp-solution-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

Create the state bucket first:
```bash
aws s3api create-bucket --bucket erp-solution-terraform-state --region us-east-1
aws dynamodb create-table --table-name terraform-state-lock ...
```

## Cleanup

To destroy infrastructure:

```bash
terraform destroy -var-file=environments/dev.tfvars
```

**Warning**: This will delete ALL resources including databases. Ensure you have backups!

## Troubleshooting

### Common Issues

1. **"Provider not found"**: Run `terraform init`
2. **"State lock error"**: Run `terraform force-unlock <LOCK_ID>`
3. **"Permission denied"**: Check AWS IAM permissions
4. **"Resource already exists"**: Import existing resources or change identifiers

### Getting Help

- Terraform Documentation: https://www.terraform.io/docs
- AWS Provider Documentation: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- Internal Team: #infrastructure Slack channel

## Next Steps

After provisioning infrastructure:

1. Update Kubernetes manifests with new RDS/Redis endpoints
2. Configure External Secrets Operator for secret management
3. Deploy applications using Kustomize overlays
4. Set up monitoring and alerting
