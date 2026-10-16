# Provider-neutral compute contract.
#
# Declares the runtime interface (placement, scaling, identity) that backend
# and frontend workloads require. Resources are instantiated in the
# environment layer after a provider is selected.

variable "environment" {
  description = "Deployment environment identifier."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "environment must be dev, staging, or production."
  }
}

variable "name_prefix" {
  description = "Prefix applied to every compute resource name."
  type        = string
}

variable "private_subnet_ids" {
  description = "Subnets that host application workloads."
  type        = list(string)
  default     = []
}

variable "backend_instance_count" {
  description = "Number of backend instances; production requires at least two."
  type        = number
  default     = 2

  validation {
    condition     = var.backend_instance_count >= 1
    error_message = "backend_instance_count must be at least 1."
  }
}

variable "frontend_instance_count" {
  description = "Number of frontend instances."
  type        = number
  default     = 2

  validation {
    condition     = var.frontend_instance_count >= 1
    error_message = "frontend_instance_count must be at least 1."
  }
}

variable "cpu_units" {
  description = "CPU entitlement per backend instance."
  type        = number
  default     = 512
}

variable "memory_mib" {
  description = "Memory entitlement per backend instance."
  type        = number
  default     = 1024
}

variable "autoscaling_enabled" {
  description = "Whether compute autoscales on load."
  type        = bool
  default     = true
}

# --- contract outputs -------------------------------------------------------

output "environment" {
  description = "Echo of the resolved environment."
  value       = var.environment
}

output "backend_instance_count" {
  description = "Requested backend instance count."
  value       = var.backend_instance_count
}

output "frontend_instance_count" {
  description = "Requested frontend instance count."
  value       = var.frontend_instance_count
}

output "autoscaling_enabled" {
  description = "Whether autoscaling is required for this environment."
  value       = var.autoscaling_enabled
}

output "instance_ids" {
  description = "Assigned by provider; empty until a provider implementation is supplied."
  value       = []
}

output "load_balancer_id" {
  description = "Assigned by provider; null until a provider implementation is supplied."
  value       = null
}
