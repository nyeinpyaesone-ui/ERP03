variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "db_name" {
  type    = string
  default = "erp_db"
}

variable "db_username" {
  type    = string
  default = "erp_admin"
}

variable "db_password_secret_arn" {
  type      = string
  sensitive = true
}

variable "instance_class" {
  type    = string
  default = "db.t3.medium"
}

variable "multi_az" {
  type    = bool
  default = false
}

variable "allocated_storage" {
  type    = number
  default = 100
}

variable "max_allocated_storage" {
  type    = number
  default = 500
}

resource "aws_db_subnet_group" "main" {
  name       = "erp-${var.environment}-db-subnet-group"
  subnet_ids = var.subnet_ids
  tags = {
    Name        = "erp-${var.environment}-db-subnet-group"
    Environment = var.environment
  }
}

resource "aws_security_group" "rds" {
  name        = "erp-${var.environment}-rds-sg"
  description = "Security group for RDS instance"
  vpc_id      = var.vpc_id
  tags = {
    Name        = "erp-${var.environment}-rds-sg"
    Environment = var.environment
  }
}

resource "aws_security_group_rule" "ingress_from_vpc" {
  type              = "ingress"
  from_port         = 5432
  to_port           = 5432
  protocol          = "tcp"
  cidr_blocks       = ["10.0.0.0/8"]
  security_group_id = aws_security_group.rds.id
}

resource "aws_security_group_rule" "egress_all" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.rds.id
}

data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = var.db_password_secret_arn
}

resource "aws_db_instance" "main" {
  identifier                  = "erp-${var.environment}-postgres"
  engine                      = "postgres"
  engine_version              = "16"
  instance_class              = var.instance_class
  db_name                     = var.db_name
  username                    = var.db_username
  password                    = data.aws_secretsmanager_secret_version.db_password.secret_string
  vpc_security_group_ids      = [aws_security_group.rds.id]
  db_subnet_group_name        = aws_db_subnet_group.main.name
  multi_az                    = var.multi_az
  allocated_storage            = var.allocated_storage
  max_allocated_storage        = var.max_allocated_storage
  storage_type                 = "gp3"
  storage_encrypted            = true
  backup_retention_period      = var.environment == "dev" ? 1 : 30
  skip_final_snapshot          = var.environment == "dev"
  final_snapshot_identifier    = var.environment == "dev" ? null : "erp-${var.environment}-final-snapshot"
  auto_minor_version_upgrade   = true
  deletion_protection          = var.environment != "dev"
  copy_tags_to_snapshot        = true
  publicly_accessible          = false
  apply_immediately             = var.environment == "dev"
  tags = {
    Name        = "erp-${var.environment}-postgres"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

output "db_endpoint" {
  value = aws_db_instance.main.endpoint
}

output "db_instance_id" {
  value = aws_db_instance.main.identifier
}

output "security_group_id" {
  value = aws_security_group.rds.id
}
