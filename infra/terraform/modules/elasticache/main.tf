variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "node_type" {
  type    = string
  default = "cache.t3.medium"
}

variable "num_cache_nodes" {
  type    = number
  default = 2
}

variable "cluster_mode_enabled" {
  type    = bool
  default = false
}

variable "num_node_groups" {
  type    = number
  default = 1
}

variable "replicas_per_node_group" {
  type    = number
  default = 1
}

variable "auth_token" {
  type      = string
  sensitive = true
}

variable "snapshot_retention_limit" {
  type    = number
  default = 7
}

resource "aws_elasticache_subnet_group" "main" {
  name       = "erp-${var.environment}-redis-subnet-group"
  subnet_ids = var.subnet_ids
  tags = {
    Name        = "erp-${var.environment}-redis-subnet-group"
    Environment = var.environment
  }
}

resource "aws_security_group" "redis" {
  name        = "erp-${var.environment}-redis-sg"
  description = "Security group for ElastiCache Redis"
  vpc_id      = var.vpc_id
  tags = {
    Name        = "erp-${var.environment}-redis-sg"
    Environment = var.environment
  }
}

resource "aws_security_group_rule" "ingress_from_vpc" {
  type              = "ingress"
  from_port         = 6379
  to_port           = 6379
  protocol          = "tcp"
  cidr_blocks       = ["10.0.0.0/8"]
  security_group_id = aws_security_group.redis.id
}

resource "aws_security_group_rule" "egress_all" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.redis.id
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "erp-${var.environment}-redis"
  description                = "ERP Redis cluster for ${var.environment}"
  node_type                  = var.node_type
  num_cache_clusters         = var.cluster_mode_enabled ? null : var.num_cache_nodes
  num_node_groups            = var.cluster_mode_enabled ? var.num_node_groups : null
  replicas_per_node_group    = var.cluster_mode_enabled ? var.replicas_per_node_group : null
  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = [aws_security_group.redis.id]
  engine                     = "redis"
  engine_version             = "7.1"
  port                       = 6379
  parameter_group_name       = "default.redis7"
  automatic_failover_enabled = var.num_cache_nodes > 1 || (var.cluster_mode_enabled && var.replicas_per_node_group > 0)
  multi_az_enabled           = var.num_cache_nodes > 1 || var.cluster_mode_enabled
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.auth_token
  auth_token_update_strategy = "ROTATE"
  maintenance_window         = "sun:05:00-sun:09:00"
  snapshot_window            = "03:00-04:00"
  snapshot_retention_limit   = var.snapshot_retention_limit
  apply_immediately          = var.environment == "dev"
  auto_minor_version_upgrade = true

  tags = {
    Name        = "erp-${var.environment}-redis"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

output "redis_endpoint" {
  value = var.cluster_mode_enabled ? aws_elasticache_replication_group.main.configuration_endpoint_address : aws_elasticache_replication_group.main.primary_endpoint_address
}

output "redis_reader_endpoint" {
  value = aws_elasticache_replication_group.main.reader_endpoint_address
}

output "security_group_id" {
  value = aws_security_group.redis.id
}
