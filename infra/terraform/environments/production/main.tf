# Production Environment Configuration

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Configure a remote backend before any shared production apply.
  # Use an encrypted, access-controlled backend with state locking.
  # backend "s3" {
  #   bucket         = "erp-solution-terraform-state"
  #   key            = "production/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = "production"
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
  default     = "10.2.0.0/16"
}

module "vpc" {
  source = "../../modules/vpc"

  vpc_cidr           = var.vpc_cidr
  environment        = "production"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  enable_nat_gateway = true
  single_nat_gateway = false
}

resource "aws_security_group" "rds" {
  name        = "prod-erp-rds-sg"
  description = "Security group for RDS"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = []
    cidr_blocks     = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "redis" {
  name        = "prod-erp-redis-sg"
  description = "Security group for Redis"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = []
    cidr_blocks     = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_elasticache_subnet_group" "main" {
  name       = "prod-erp-cache-subnet-group"
  subnet_ids = module.vpc.private_subnet_ids
}

module "rds" {
  source = "../../modules/rds"

  identifier              = "prod-erp-db"
  db_name                 = "erpdb"
  username                = "erpadmin"
  password                = var.db_password
  instance_class          = "db.r6g.xlarge"
  allocated_storage       = 200
  max_allocated_storage   = 1000
  multi_az                = true
  vpc_security_group_ids  = [aws_security_group.rds.id]
  db_subnet_group_name    = ""
  environment             = "production"
  backup_retention_period = 30
}

module "elasticache" {
  source = "../../modules/elasticache"

  cluster_id              = "prod-erp-redis"
  node_type               = "cache.r6g.large"
  num_cache_nodes         = 6
  parameter_group_name    = ""
  subnet_group_name       = aws_elasticache_subnet_group.main.name
  security_group_ids      = [aws_security_group.redis.id]
  snapshot_retention_limit = 30
}

resource "aws_s3_bucket" "backups" {
  bucket = "prod-erp-backups-${random_id.bucket_suffix.hex}"
}

resource "random_id" "bucket_suffix" {
  byte_length = 8
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "backup-retention"
    status = "Enabled"
    filter { prefix = "" }
    expiration { days = 90 }
  }

  rule {
    id     = "glacier-transition"
    status = "Enabled"
    filter { prefix = "" }
    transition {
      days          = 30
      storage_class = "GLACIER"
    }
  }
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

output "vpc_id" {
  value = module.vpc.vpc_id
}
