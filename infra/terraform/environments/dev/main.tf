# ERP03 dev environment root.
#
# Provider-neutral: resources are instantiated by the selected provider in the
# environment layer. Values below are the approved dev contract.

terraform {
  required_version = ">= 1.9.0, < 2.0.0"
}

module "networking" {
  source = "../../modules/networking"

  environment          = "dev"
  name_prefix          = "erp03-dev"
  vpc_cidr             = "10.20.0.0/16"
  availability_zones   = ["a", "b"]
  private_subnet_cidrs = ["10.20.1.0/24", "10.20.2.0/24"]
  public_subnet_cidrs  = ["10.20.101.0/24", "10.20.102.0/24"]
  enable_flow_logs     = false
  enable_nat_gateway   = false
}

module "compute" {
  source = "../../modules/compute"

  environment             = "dev"
  name_prefix             = "erp03-dev"
  private_subnet_ids      = module.networking.private_subnet_ids
  backend_instance_count  = 1
  frontend_instance_count = 1
  cpu_units               = 256
  memory_mib              = 512
  autoscaling_enabled     = false
}

module "database" {
  source = "../../modules/database"

  environment           = "dev"
  name_prefix           = "erp03-dev"
  multi_az              = false
  deletion_protection   = false
  backup_retention_days = 7
  private_subnet_ids    = module.networking.private_subnet_ids
}

module "monitoring" {
  source = "../../modules/monitoring"

  environment            = "dev"
  name_prefix            = "erp03-dev"
  metrics_retention_days = 15
  log_retention_days     = 30
}

output "environment" {
  description = "Resolved environment for this root."
  value       = "dev"
}

output "network" {
  description = "Networking contract for dev."
  value       = module.networking
}

output "data" {
  description = "Database contract for dev."
  value = {
    engine    = module.database.postgres_version
    encrypted = module.database.storage_encrypted
    retention = module.database.backup_retention_days
  }
}
