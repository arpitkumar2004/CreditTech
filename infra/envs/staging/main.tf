terraform {
  # Configure a real remote backend before first `terraform init`.
  # backend "s3" {
  #   bucket         = "credittech-tfstate"
  #   key            = "staging/terraform.tfstate"
  #   region         = "ap-south-1"
  #   dynamodb_table = "credittech-tfstate-lock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = "ap-south-1"
  default_tags {
    tags = {
      Project = "credittech"
      Env     = "staging"
      Owner   = "platform"
    }
  }
}

module "network" {
  source = "../../modules/network"
  env    = "staging"
}

module "database" {
  source                = "../../modules/database"
  env                   = "staging"
  vpc_id                = module.network.vpc_id
  subnet_ids            = module.network.private_subnet_ids
  app_security_group_id = module.network.app_security_group_id
}

module "storage" {
  source = "../../modules/storage"
  env    = "staging"
}

variable "container_image" {
  type        = string
  description = "ECR image URI for the core service"
  default     = "public.ecr.aws/docker/library/hello-world:latest"
}

variable "database_url_secret_arn" {
  type        = string
  description = "Secrets Manager ARN for the DATABASE_URL used by ECS"
  default     = ""
}

module "container_app" {
  source                  = "../../modules/container_app"
  env                     = "staging"
  image                   = var.container_image
  subnet_ids              = module.network.private_subnet_ids
  security_group_id       = module.network.app_security_group_id
  database_url_secret_arn = var.database_url_secret_arn
}

output "db_endpoint" {
  value = module.database.endpoint
}

output "artefact_bucket" {
  value = module.storage.bucket_name
}
