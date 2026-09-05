terraform {
  # backend "s3" {
  #   bucket         = "credittech-tfstate"
  #   key            = "production/terraform.tfstate"
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
      Env     = "production"
      Owner   = "platform"
    }
  }
}

module "network" {
  source   = "../../modules/network"
  env      = "production"
  vpc_cidr = "10.30.0.0/16"
}

module "database" {
  source                = "../../modules/database"
  env                   = "production"
  vpc_id                = module.network.vpc_id
  subnet_ids            = module.network.private_subnet_ids
  app_security_group_id = module.network.app_security_group_id
  instance_class        = "db.t4g.medium"
  allocated_storage_gb  = 50
}

module "storage" {
  source = "../../modules/storage"
  env    = "production"
}

variable "container_image" {
  type = string
}

variable "database_url_secret_arn" {
  type = string
}

module "container_app" {
  source                  = "../../modules/container_app"
  env                     = "production"
  image                   = var.container_image
  subnet_ids              = module.network.private_subnet_ids
  security_group_id       = module.network.app_security_group_id
  database_url_secret_arn = var.database_url_secret_arn
  cpu                     = 1024
  memory                  = 2048
}

output "db_endpoint" {
  value     = module.database.endpoint
  sensitive = true
}
