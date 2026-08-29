variable "db_password_secret_arn" {
  description = "AWS Secrets Manager ARN containing the RDS master password"
  type        = string
  sensitive   = true
}

variable "redis_auth_token" {
  description = "Redis AUTH token supplied securely by CI/secret management"
  type        = string
  sensitive   = true
}
