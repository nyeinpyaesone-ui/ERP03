# Staging Environment Configuration

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = "staging"
      Project     = "erp_solution"
      ManagedBy   = "terraform"
    }
  }
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.1.0.0/16"
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"
  
  vpc_cidr           = var.vpc_cidr
  environment        = "staging"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  enable_nat_gateway = true
  single_nat_gateway = false
}

# Security Group for RDS
resource "aws_security_group" "rds" {
  name        = "staging-erp-rds-sg"
  description = "Security group for RDS"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = []
    cidr_blocks     = ["10.1.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "staging-erp-rds-sg"
  }
}

# Security Group for ElastiCache
resource "aws_security_group" "redis" {
  name        = "staging-erp-redis-sg"
  description = "Security group for ElastiCache"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = []
    cidr_blocks     = ["10.1.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "staging-erp-redis-sg"
  }
}

# Subnet Group for ElastiCache
resource "aws_elasticache_subnet_group" "main" {
  name       = "staging-erp-cache-subnet-group"
  subnet_ids = module.vpc.private_subnet_ids

  tags = {
    Name = "staging-erp-cache-subnet-group"
  }
}

# RDS Module
module "rds" {
  source = "../../modules/rds"
  
  identifier               = "staging-erp-db"
  db_name                  = "erpdb"
  username                 = "erpadmin"
  password                 = var.db_password
  instance_class           = "db.r6g.large"
  allocated_storage        = 100
  multi_az                 = true
  vpc_security_group_ids   = [aws_security_group.rds.id]
  db_subnet_group_name     = ""
  environment              = "staging"
}

# ElastiCache Module
module "elasticache" {
  source = "../../modules/elasticache"
  
  cluster_id           = "staging-erp-redis"
  node_type            = "cache.r6g.medium"
  num_cache_nodes      = 3
  parameter_group_name = ""
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]
  environment          = "staging"
}

# S3 Bucket for Backups
resource "aws_s3_bucket" "backups" {
  bucket = "staging-erp-backups-${random_id.bucket_suffix.hex}"
  
  tags = {
    Name        = "staging-erp-backups"
    Environment = "staging"
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "backup-retention"
    status = "Enabled"

    expiration {
      days = 30
    }

    filter {
      prefix = ""
    }
  }
}

# Outputs
output "vpc_id" {
  value = module.vpc.vpc_id
}

output "private_subnet_ids" {
  value = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  value = module.vpc.public_subnet_ids
}

output "rds_endpoint" {
  value     = module.rds.endpoint
  sensitive = true
}

output "redis_primary_endpoint" {
  value = module.elasticache.primary_endpoint_address
}

output "backup_bucket" {
  value = aws_s3_bucket.backups.bucket
}
