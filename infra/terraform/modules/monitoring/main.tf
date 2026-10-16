# Provider-neutral monitoring contract.
#
# Declares the observability interface: metrics retention, log aggregation,
# dashboards and alert routing that Section 10 requires. Concrete backing
# services are chosen in the environment layer.

variable "environment" {
  description = "Deployment environment identifier."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "environment must be dev, staging, or production."
  }
}

variable "name_prefix" {
  description = "Prefix applied to every observability resource name."
  type        = string
}

variable "metrics_retention_days" {
  description = "How long metrics are queryable."
  type        = number
  default     = 30

  validation {
    condition     = var.metrics_retention_days >= 15
    error_message = "metrics_retention_days must be at least 15 for incident forensics."
  }
}

variable "log_retention_days" {
  description = "How long centralized logs are searchable."
  type        = number
  default     = 30

  validation {
    condition     = var.log_retention_days >= 30
    error_message = "log_retention_days must be at least 30."
  }
}

variable "log_indexing_enabled" {
  description = "Whether logs are indexed for search by request identifier."
  type        = bool
  default     = true
}

variable "alert_notification_targets" {
  description = "Notification destinations for alert routing, supplied by the operator."
  type        = list(string)
  default     = []
}

variable "error_rate_threshold_percent" {
  description = "5xx ratio that raises a saturation/error alert."
  type        = number
  default     = 2

  validation {
    condition     = var.error_rate_threshold_percent > 0 && var.error_rate_threshold_percent < 100
    error_message = "error_rate_threshold_percent must be between 0 and 100."
  }
}

variable "latency_p95_threshold_ms" {
  description = "p95 latency that raises a latency alert."
  type        = number
  default     = 800

  validation {
    condition     = var.latency_p95_threshold_ms > 0
    error_message = "latency_p95_threshold_ms must be positive."
  }
}

variable "dashboard_names" {
  description = "Dashboards that must exist for this environment."
  type        = list(string)
  default     = ["service-health", "database-health", "saturation"]
}

# --- contract outputs -------------------------------------------------------

output "environment" {
  description = "Echo of the resolved environment."
  value       = var.environment
}

output "metrics_retention_days" {
  description = "Metrics retention window."
  value       = var.metrics_retention_days
}

output "log_retention_days" {
  description = "Log retention window."
  value       = var.log_retention_days
}

output "alert_thresholds" {
  description = "Alerting thresholds resolved for this environment."
  value = {
    error_rate_percent = var.error_rate_threshold_percent
    latency_p95_ms     = var.latency_p95_threshold_ms
  }
}

output "dashboard_names" {
  description = "Required dashboards."
  value       = var.dashboard_names
}

output "metrics_endpoint" {
  description = "Assigned by provider; null until a provider implementation is supplied."
  value       = null
}
