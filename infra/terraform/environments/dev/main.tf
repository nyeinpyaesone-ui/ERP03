terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = { source = "hashicorp/aws"; version = "~> 5.0" }
  }
}

provider "aws" {
  region = "ap-southeast-1"
  default_tags {
    tags = {
      Project   = "erp-backend"
      ManagedBy = "terraform"
      Environment = "dev"
    }
  }
}

module "vpc" {
  source = "../../modules/vpc"
  environment = "dev"
  vpc_cidr = "10.0.0.0/16"
  availability_zones = ["ap-southeast-1a", "ap-southeast-1b"]
  single_nat_gateway = true
}

module "rds" {
  source = "../../modules/rds"
  environment = "dev"
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
  db_name = "erp_dev"
  db_username = "erp_admin"
  db_password_secret_arn = aws_secretsmanager_secret.db_password.arn
  instance_class = "db.t3.small"
  multi_az = false
  allocated_storage = 50
}

module "elasticache" {
  source = "../../modules/elasticache"
  environment = "dev"
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
  node_type = "cache.t3.small"
  num_cache_nodes = 2
  cluster_mode_enabled = false
}

resource "aws_secretsmanager_secret" "db_password" {
  name = "erp/dev/db-password"
  description = "Development database password"
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  generate_password = true
}

output "vpc_id" { value = module.vpc.vpc_id }
output "db_endpoint" { value = module.rds.db_endpoint }
output "redis_endpoint" { value = module.elasticache.redis_endpoint }
