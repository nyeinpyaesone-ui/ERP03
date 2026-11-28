terraform {
  required_version = ">= 1.9.0, < 2.0.0"
}

variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "environment must be dev, staging, or production"
  }
}

variable "project_name" {
  type    = string
  default = "erp03"
}

output "environment" {
  value = var.environment
}

output "project_name" {
  value = var.project_name
}
