# ERP Solution Infrastructure

This directory contains Terraform configurations for provisioning cloud infrastructure.

## Structure

```
terraform/
├── modules/                 # Reusable Terraform modules
│   ├── vpc/                # VPC and networking
│   ├── eks/                # Kubernetes cluster (EKS/GKE)
│   ├── rds/                # Managed PostgreSQL (RDS/Cloud SQL)
│   └── elasticache/        # Managed Redis (ElastiCache/Memorystore)
├── environments/           # Environment-specific configurations
│   ├── dev/               # Development environment
│   ├── staging/           # Staging environment
│   └── production/        # Production environment
└── backend.tf             # Remote state configuration (to be added)
```

## Getting Started

### Prerequisites
- Terraform >= 1.5.0
- AWS CLI / GCP CLI configured with appropriate credentials
- kubectl configured for target cluster

### Initial Setup (TO DO)

1. **Initialize Backend** (for remote state storage):
   ```bash
   # Create S3 bucket and DynamoDB table for state locking
   # Then configure backend.tf
   ```

2. **Initialize Terraform**:
   ```bash
   cd environments/production
   terraform init
   ```

3. **Plan and Apply**:
   ```bash
   terraform plan -out=tfplan
   terraform apply tfplan
   ```

## Modules to Implement

### 1. VPC Module (`modules/vpc`)
- VPC with public/private subnets
- Internet Gateway and NAT Gateway
- Route tables
- Security groups

### 2. EKS Module (`modules/eks`)
- EKS cluster with managed node groups
- IAM roles and policies
- OIDC provider for IRSA
- Cluster autoscaler configuration

### 3. RDS Module (`modules/rds`)
- PostgreSQL instance (managed)
- Multi-AZ for production
- Automated backups
- Parameter groups

### 4. ElastiCache Module (`modules/elasticache`)
- Redis cluster (managed)
- Multi-AZ replication group
- Parameter groups
- Subnet groups

## Migration from Current Setup

Current Kubernetes manifests use StatefulSets for PostgreSQL and Redis. These should be:
1. **Replaced with managed services** (RDS/ElastiCache or Cloud SQL/Memorystore)
2. **Remove StatefulSets** from `infra/k8s/base/postgres.yaml` and `redis.yaml`
3. **Update connection strings** in ConfigMap/Secrets to point to managed services

## Security Considerations

- Use AWS Secrets Manager or HashiCorp Vault for sensitive values
- Enable encryption at rest for all datastores
- Implement least-privilege IAM policies
- Use private subnets for databases and cache
- Enable VPC Flow Logs for network monitoring

## Next Steps

1. [ ] Implement VPC module
2. [ ] Implement EKS module  
3. [ ] Implement RDS module (replace StatefulSet)
4. [ ] Implement ElastiCache module (replace StatefulSet)
5. [ ] Configure remote state backend
6. [ ] Add CI/CD integration for Terraform
7. [ ] Document migration path from current setup
