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

  # Configure a remote encrypted backend with state locking before shared production apply.
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
  type    = string
  default = "us-east-1"
}

variable "vpc_cidr" {
  type    = string
  default = "10.2.0.0/16"
}

variable "db_password_secret_arn" {
  type      = string
  sensitive = true
}

variable "redis_auth_token" {
  type      = string
  sensitive = true
}

module "vpc" {
  source = "../../modules/vpc"

  vpc_cidr           = var.vpc_cidr
  environment        = "production"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  single_nat_gateway = false
}

module "rds" {
  source = "../../modules/rds"

  environment             = "production"
  vpc_id                  = module.vpc.vpc_id
  subnet_ids              = module.vpc.private_subnet_ids
  db_name                 = "erpdb"
  db_username             = "erpadmin"
  db_password_secret_arn  = var.db_password_secret_arn
  instance_class          = "db.r6g.xlarge"
  allocated_storage       = 200
  max_allocated_storage   = 1000
  multi_az                = true
}

module "elasticache" {
  source = "../../modules/elasticache"

  environment             = "production"
  vpc_id                  = module.vpc.vpc_id
  subnet_ids              = module.vpc.private_subnet_ids
  node_type               = "cache.r6g.large"
  num_cache_nodes         = 2
  auth_token              = var.redis_auth_token
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

    filter {
      prefix = ""
    }

    expiration {
      days = 90
    }
  }

  rule {
    id     = "glacier-transition"
    status = "Enabled"

    filter {
      prefix = ""
    }

    transition {
      days          = 30
      storage_class = "GLACIER"
    }
  }
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id

  versioning_configuration {
    status = "Enabled"
  }
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

output "rds_endpoint" {
  value = module.rds.db_endpoint
}

output "redis_endpoint" {
  value = module.elasticache.redis_endpoint
}
