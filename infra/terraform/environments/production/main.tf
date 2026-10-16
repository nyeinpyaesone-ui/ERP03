# ERP03 production environment root.
#
# Production defaults: high availability, encrypted storage, deletion
# protection, long backup retention, and full observability retention.

terraform {
  required_version = ">= 1.9.0, < 2.0.0"
}

module "networking" {
  source = "../../modules/networking"

  environment          = "production"
  name_prefix          = "erp03-prod"
  vpc_cidr             = "10.40.0.0/16"
  availability_zones   = ["a", "b", "c"]
  private_subnet_cidrs = ["10.40.1.0/24", "10.40.2.0/24", "10.40.3.0/24"]
  public_subnet_cidrs  = ["10.40.101.0/24", "10.40.102.0/24", "10.40.103.0/24"]
  enable_flow_logs     = true
  enable_nat_gateway   = true
}

module "compute" {
  source = "../../modules/compute"

  environment             = "production"
  name_prefix             = "erp03-prod"
  private_subnet_ids      = module.networking.private_subnet_ids
  backend_instance_count  = 3
  frontend_instance_count = 2
  cpu_units               = 1024
  memory_mib              = 2048
  autoscaling_enabled     = true
}

module "database" {
  source = "../../modules/database"

  environment           = "production"
  name_prefix           = "erp03-prod"
  instance_class        = "db.m6g.large"
  multi_az              = true
  deletion_protection   = true
  backup_retention_days = 35
  private_subnet_ids    = module.networking.private_subnet_ids
}

module "monitoring" {
  source = "../../modules/monitoring"

  environment                  = "production"
  name_prefix                  = "erp03-prod"
  metrics_retention_days       = 90
  log_retention_days           = 90
  error_rate_threshold_percent = 1
  latency_p95_threshold_ms     = 500
  alert_notification_targets   = ["oncall-primary", "oncall-secondary"]
}

output "environment" {
  description = "Resolved environment for this root."
  value       = "production"
}

output "network" {
  description = "Networking contract for production."
  value       = module.networking
}

output "data" {
  description = "Database contract for production."
  value = {
    engine    = module.database.postgres_version
    encrypted = module.database.storage_encrypted
    retention = module.database.backup_retention_days
    multi_az  = module.database.multi_az
  }
}

output "observability" {
  description = "Monitoring contract for production."
  value       = module.monitoring.alert_thresholds
}
