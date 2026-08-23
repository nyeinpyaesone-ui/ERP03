# RDS PostgreSQL Module

Creates a managed RDS PostgreSQL instance with Multi-AZ support.

## Features

- Multi-AZ deployment for high availability
- Automated backups with configurable retention
- Encryption at rest
- Parameter group customization
- Security group with controlled access

## Usage

```hcl
module "rds" {
  source = "./modules/rds"
  
  identifier           = "erp-db"
  db_name              = "erpdb"
  username             = "erpadmin"
  password             = var.db_password
  instance_class       = "db.r6g.large"
  allocated_storage    = 100
  multi_az             = true
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
}
```

## Outputs

- `endpoint` - RDS instance endpoint
- `port` - RDS instance port
- `arn` - RDS instance ARN
