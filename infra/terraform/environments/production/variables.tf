variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
  
  # In production, use AWS Secrets Manager or SSM Parameter Store
  # Do NOT set a default value here - it must be provided securely
}

variable "redis_auth_token" {
  description = "Redis authentication token"
  type        = string
  sensitive   = true
  
  # In production, use AWS Secrets Manager or SSM Parameter Store
  # Do NOT set a default value here - it must be provided securely
}
