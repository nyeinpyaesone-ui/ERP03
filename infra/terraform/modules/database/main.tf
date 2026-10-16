# Provider-neutral database contract.
#
# Declares the transactional store interface ERP03 depends on: PostgreSQL with
# encryption, backups, and point-in-time recovery. Resource instantiation and
# engine version pinning happen in the environment layer per provider.

variable "environment" {
  description = "Deployment environment identifier."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "environment must be dev, staging, or production."
  }
}

variable "name_prefix" {
  description = "Prefix applied to every data-tier resource name."
  type        = string
}

variable "postgres_version" {
  description = "PostgreSQL major version; must match the version CI validates."
  type        = string
  default     = "15"

  validation {
    condition     = can(regex("^1[0-9]$", var.postgres_version))
    error_message = "postgres_version must be a supported major version such as 15."
  }
}

variable "instance_class" {
  description = "Database instance sizing token, provider-specific value supplied by the operator."
  type        = string
  default     = "db.t4g.medium"
}

variable "multi_az" {
  description = "Whether the database spans availability zones; required in production."
  type        = bool
  default     = false
}

variable "storage_encrypted" {
  description = "Whether data at rest is encrypted; must never be disabled."
  type        = bool
  default     = true

  validation {
    condition     = var.storage_encrypted
    error_message = "storage_encrypted cannot be disabled."
  }
}

variable "backup_retention_days" {
  description = "Days of backups retained; production requires at least 7."
  type        = number
  default     = 7

  validation {
    condition     = var.backup_retention_days >= 7
    error_message = "backup_retention_days must be at least 7."
  }
}

variable "deletion_protection" {
  description = "Whether the database may be destroyed; enabled outside dev."
  type        = bool
  default     = true
}

variable "private_subnet_ids" {
  description = "Subnets that host the database."
  type        = list(string)
  default     = []
}

variable "allowed_security_group_ids" {
  description = "Security groups permitted to reach the database port."
  type        = list(string)
  default     = []
}

# --- contract outputs -------------------------------------------------------

output "environment" {
  description = "Echo of the resolved environment."
  value       = var.environment
}

output "postgres_version" {
  description = "PostgreSQL major version requested."
  value       = var.postgres_version
}

output "storage_encrypted" {
  description = "Encryption-at-rest requirement."
  value       = var.storage_encrypted
}

output "backup_retention_days" {
  description = "Backup retention window in days."
  value       = var.backup_retention_days
}

output "deletion_protection" {
  description = "Deletion protection requirement."
  value       = var.deletion_protection
}

output "multi_az" {
  description = "Whether the database spans availability zones."
  value       = var.multi_az
}

output "instance_class" {
  description = "Database sizing token requested by this environment."
  value       = var.instance_class
}

output "endpoint" {
  description = "Assigned by provider; null until a provider implementation is supplied."
  value       = null
}

output "resource_id" {
  description = "Assigned by provider; null until a provider implementation is supplied."
  value       = null
}
