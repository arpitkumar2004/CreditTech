variable "env" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "app_security_group_id" {
  type = string
}

variable "instance_class" {
  type    = string
  default = "db.t4g.small"
}

variable "allocated_storage_gb" {
  type    = number
  default = 20
}

resource "aws_db_subnet_group" "this" {
  name       = "credittech-${var.env}"
  subnet_ids = var.subnet_ids
}

resource "aws_security_group" "db" {
  name        = "credittech-${var.env}-db"
  description = "Postgres ingress from app SG only"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
    description     = "Postgres from app tier"
  }
}

resource "aws_db_instance" "postgres" {
  identifier                  = "credittech-${var.env}"
  engine                      = "postgres"
  engine_version              = "15"
  instance_class              = var.instance_class
  allocated_storage           = var.allocated_storage_gb
  storage_encrypted           = true
  db_subnet_group_name        = aws_db_subnet_group.this.name
  vpc_security_group_ids      = [aws_security_group.db.id]
  db_name                     = "credittech"
  username                    = "credittech"
  manage_master_user_password = true
  backup_retention_period     = 14
  deletion_protection         = true
  skip_final_snapshot         = false
  final_snapshot_identifier   = "credittech-${var.env}-final"
  performance_insights_enabled = true
  auto_minor_version_upgrade  = true
}

output "endpoint" {
  value = aws_db_instance.postgres.endpoint
}
