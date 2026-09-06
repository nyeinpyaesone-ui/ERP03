# Terraform Infrastructure for ERP Backend

Complete Infrastructure as Code (IaC) for deploying ERP backend on AWS.

## Structure

```
terraform/
├── modules/           # Reusable infrastructure components
│   ├── vpc/          # VPC, subnets, routing, NAT gateways
│   ├── rds/          # Managed PostgreSQL (RDS)
│   └── elasticache/  # Managed Redis (ElastiCache)
└── environments/      # Environment-specific configurations
    ├── dev/          # Development (cost-optimized)
    ├── staging/      # Staging (production-like)
    └── production/   # Production (highly available)
```

## Quick Start

### Prerequisites
- Terraform >= 1.0
- AWS CLI configured (`aws configure`)
- IAM user with appropriate permissions

### Deploy Development Environment

```bash
cd infra/terraform/environments/dev
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### Outputs
After deployment, you'll get:
- `vpc_id`: VPC ID for Kubernetes cluster
- `db_endpoint`: RDS PostgreSQL endpoint
- `redis_endpoint`: ElastiCache Redis endpoint

Use these values in your Kubernetes configuration or `.env` file.

## Modules

### VPC Module
Creates a complete network foundation:
- Multi-AZ VPC with public/private subnets
- Internet Gateway for public access
- NAT Gateways for private subnet egress
- Route tables and associations

### RDS Module
Provisions managed PostgreSQL:
- Multi-AZ support (staging/production)
- Automated backups
- Encryption at rest
- Integration with AWS Secrets Manager

### ElastiCache Module
Deploys managed Redis:
- Cluster mode support
- Multi-AZ replication
- Encryption in transit and at rest
- Automatic failover

## Security

- All secrets stored in AWS Secrets Manager
- Security groups restrict access to VPC CIDR only
- Encryption enabled for all data stores
- No hardcoded credentials

## Cleanup

```bash
terraform destroy
```

⚠️ **Warning**: This will delete all resources including databases. Backup data first!
