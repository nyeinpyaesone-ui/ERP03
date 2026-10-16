# ERP03 staging environment root.
#
# Staging mirrors production sizing so promotion validates the real shape of
# the release before production sign-off.

terraform {
  required_version = ">= 1.9.0, < 2.0.0"
}

module "networking" {
  source = "../../modules/networking"

  environment          = "staging"
  name_prefix          = "erp03-staging"
  vpc_cidr             = "10.30.0.0/16"
  availability_zones   = ["a", "b"]
  private_subnet_cidrs = ["10.30.1.0/24", "10.30.2.0/24"]
  public_subnet_cidrs  = ["10.30.101.0/24", "10.30.102.0/24"]
  enable_flow_logs     = true
  enable_nat_gateway   = true
}

module "compute" {
  source = "../../modules/compute"

  environment             = "staging"
  name_prefix             = "erp03-staging"
  private_subnet_ids      = module.networking.private_subnet_ids
  backend_instance_count  = 2
  frontend_instance_count = 2
  cpu_units               = 512
  memory_mib              = 1024
  autoscaling_enabled     = true
}

module "database" {
  source = "../../modules/database"

  environment           = "staging"
  name_prefix           = "erp03-staging"
  instance_class        = "db.t4g.medium"
  multi_az              = false
  deletion_protection   = true
  backup_retention_days = 14
  private_subnet_ids    = module.networking.private_subnet_ids
}

module "monitoring" {
  source = "../../modules/monitoring"

  environment                  = "staging"
  name_prefix                  = "erp03-staging"
  metrics_retention_days       = 30
  log_retention_days           = 30
  error_rate_threshold_percent = 2
  latency_p95_threshold_ms     = 800
}

output "environment" {
  description = "Resolved environment for this root."
  value       = "staging"
}

output "network" {
  description = "Networking contract for staging."
  value       = module.networking
}

output "data" {
  description = "Database contract for staging."
  value = {
    engine    = module.database.postgres_version
    encrypted = module.database.storage_encrypted
    retention = module.database.backup_retention_days
    multi_az  = module.database.multi_az
  }
}
