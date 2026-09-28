variable "aws_region" {
  description = "Região AWS onde os recursos serão criados"
  type        = string
  default     = "us-east-2"
}

variable "project_name" {
  description = "Nome do projeto"
  type        = string
  default     = "football-data-engineering"
}

variable "environment" {
  description = "Ambiente do projeto"
  type        = string
  default     = "dev"
}