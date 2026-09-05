variable "env" {
  type = string
}

variable "image" {
  type        = string
  description = "Container image URI (e.g. ECR repo + tag)"
}

variable "subnet_ids" {
  type = list(string)
}

variable "security_group_id" {
  type = string
}

variable "database_url_secret_arn" {
  type        = string
  description = "Secrets Manager ARN for DATABASE_URL"
}

variable "cpu" {
  type    = number
  default = 512
}

variable "memory" {
  type    = number
  default = 1024
}

resource "aws_ecs_cluster" "this" {
  name = "credittech-${var.env}"
}

resource "aws_ecs_task_definition" "app" {
  family                   = "credittech-${var.env}-app"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory

  container_definitions = jsonencode([
    {
      name      = "core"
      image     = var.image
      essential = true
      portMappings = [{ containerPort = 8000, protocol = "tcp" }]
      secrets = [
        { name = "DATABASE_URL", valueFrom = var.database_url_secret_arn },
      ]
      environment = [
        { name = "APP_ENV",     value = var.env },
        { name = "LOG_FORMAT",  value = "json" },
      ]
      healthCheck = {
        command  = ["CMD-SHELL", "curl -fsS http://localhost:8000/health || exit 1"]
        interval = 30
        timeout  = 5
        retries  = 3
      }
    }
  ])
}

resource "aws_ecs_service" "app" {
  name            = "credittech-${var.env}-app"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [var.security_group_id]
    assign_public_ip = false
  }

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
}

output "cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "service_name" {
  value = aws_ecs_service.app.name
}
