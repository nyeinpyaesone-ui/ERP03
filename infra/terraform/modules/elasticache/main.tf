variable "cluster_id" {
  description = "ElastiCache cluster identifier"
  type        = string
}

variable "node_type" {
  description = "Cache node type"
  type        = string
  default     = "cache.r6g.large"
}

variable "num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 3
}

variable "engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

variable "port" {
  description = "Redis port"
  type        = number
  default     = 6379
}

variable "parameter_group_name" {
  description = "Parameter group name"
  type        = string
  default     = ""
}

variable "subnet_group_name" {
  description = "Subnet group name"
  type        = string
}

variable "security_group_ids" {
  description = "List of security group IDs"
  type        = list(string)
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "snapshot_retention_limit" {
  description = "Snapshot retention period in days"
  type        = number
  default     = 30
}

variable "maintenance_window" {
  description = "Maintenance window"
  type        = string
  default     = "mon:04:00-mon:05:00"
}

locals {
  common_tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
    Project     = "erp_solution"
  }
}

# Parameter Group
resource "aws_elasticache_parameter_group" "main" {
  count  = var.parameter_group_name == "" ? 1 : 0
  family = "redis${split(".", var.engine_version)[0]}"
  name   = "${var.cluster_id}-params"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  tags = merge(local.common_tags, {
    Name = "${var.cluster_id}-params"
  })
}

# Replication Group (Cluster Mode Enabled)
resource "aws_elasticache_replication_group" "main" {
  replication_group_id          = var.cluster_id
  description                   = "ERP Redis Cluster"
  
  engine                        = "redis"
  engine_version                = var.engine_version
  node_type                     = var.node_type
  num_node_groups               = 1
  replicas_per_node_group       = var.num_cache_nodes - 1
  port                          = var.port
  
  parameter_group_name          = var.parameter_group_name != "" ? var.parameter_group_name : aws_elasticache_parameter_group.main[0].name
  subnet_group_name             = var.subnet_group_name
  security_group_ids            = var.security_group_ids
  
  automatic_failover_enabled    = true
  multi_az_enabled              = true
  
  at_rest_encryption_enabled    = true
  transit_encryption_enabled    = true
  auth_token_update_strategy    = "ROTATE_CURRENT"
  
  snapshot_retention_limit      = var.snapshot_retention_limit
  snapshot_window               = "02:00-03:00"
  maintenance_window            = var.maintenance_window
  
  auto_minor_version_upgrade    = true
  
  notification_topic_arn        = null # TODO: Add SNS topic for alerts
  
  tags = merge(local.common_tags, {
    Name = var.cluster_id
  })

  lifecycle {
    prevent_destroy = true
  }
}

output "primary_endpoint_address" {
  description = "Primary endpoint address"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "reader_endpoint_address" {
  description = "Reader endpoint address"
  value       = aws_elasticache_replication_group.reader_endpoint_address
}

output "arn" {
  description = "Cache cluster ARN"
  value       = aws_elasticache_replication_group.main.arn
}

output "configuration_endpoint_address" {
  description = "Configuration endpoint address"
  value       = aws_elasticache_replication_group.main.configuration_endpoint_address
}

output "port" {
  description = "Redis port"
  value       = aws_elasticache_replication_group.main.port
}
