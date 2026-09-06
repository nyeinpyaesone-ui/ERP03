variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
  
  # In production, use AWS Secrets Manager or SSM Parameter Store
  default = "ChangeMeInProduction123!"
}
