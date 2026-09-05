variable "env" {
  type        = string
  description = "Environment name (staging | production)"
}

variable "region" {
  type        = string
  default     = "ap-south-1"
  description = "India region (data-localisation intent, ADR-5)"
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "credittech-${var.env}"
    Env  = var.env
  }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = "${var.region}${count.index == 0 ? "a" : "b"}"

  tags = {
    Name = "credittech-${var.env}-private-${count.index}"
    Env  = var.env
    Tier = "private"
  }
}

resource "aws_security_group" "app" {
  name        = "credittech-${var.env}-app"
  description = "CreditTech app egress to managed services only"
  vpc_id      = aws_vpc.this.id

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS egress for AA / geospatial / bureau connectors"
  }
}

output "vpc_id" {
  value = aws_vpc.this.id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "app_security_group_id" {
  value = aws_security_group.app.id
}
