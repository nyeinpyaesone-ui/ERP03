# Provider-neutral networking contract.
#
# This module declares the interface an environment must satisfy for network
# isolation. No cloud resources are instantiated here: the provider, region and
# CIDR allocations are operator decisions applied in the environment layer once
# a provider is selected. Outputs marked "assigned by provider" are null or
# empty until that implementation exists, so plans stay honest.

variable "environment" {
  description = "Deployment environment identifier."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "environment must be dev, staging, or production."
  }
}

variable "name_prefix" {
  description = "Prefix applied to every network resource name."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,30}$", var.name_prefix))
    error_message = "name_prefix must be 3-30 lowercase alphanumeric or hyphen characters and start with a letter."
  }
}

variable "vpc_cidr" {
  description = "Primary CIDR block for the network."
  type        = string

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "vpc_cidr must be a valid IPv4 CIDR block."
  }
}

variable "availability_zones" {
  description = "Availability zones spread across subnets; at least two for failure tolerance."
  type        = list(string)

  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "at least two availability zones are required for production-grade redundancy."
  }
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for application/data subnets."
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for ingress/egress subnets."
  type        = list(string)
}

variable "enable_flow_logs" {
  description = "Whether network flow logs are retained for audit."
  type        = bool
  default     = true
}

variable "enable_nat_gateway" {
  description = "Whether egress traffic leaves through a NAT gateway."
  type        = bool
  default     = true
}

# --- contract outputs -------------------------------------------------------

output "environment" {
  description = "Echo of the resolved environment."
  value       = var.environment
}

output "vpc_cidr" {
  description = "Primary CIDR block for the network."
  value       = var.vpc_cidr
}

output "private_subnet_cidrs" {
  description = "CIDR blocks allocated to application/data subnets."
  value       = var.private_subnet_cidrs
}

output "public_subnet_cidrs" {
  description = "CIDR blocks allocated to ingress/egress subnets."
  value       = var.public_subnet_cidrs
}

output "availability_zones" {
  description = "Zones the network spans."
  value       = var.availability_zones
}

output "flow_logs_enabled" {
  description = "Whether flow logs are required by this environment."
  value       = var.enable_flow_logs
}

output "vpc_id" {
  description = "Assigned by provider; null until a provider implementation is supplied."
  value       = null
}

output "private_subnet_ids" {
  description = "Assigned by provider; empty until a provider implementation is supplied."
  value       = []
}

output "public_subnet_ids" {
  description = "Assigned by provider; empty until a provider implementation is supplied."
  value       = []
}
