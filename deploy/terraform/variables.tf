# Terraform variables for Smart LINE Bot

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "smart-line-bot"
}

variable "environment" {
  description = "Environment (production/staging/development)"
  type        = string
  default     = "production"
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "demo_project"
  sensitive   = true
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "postgres"
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# LINE API Credentials
variable "line_channel_access_token" {
  description = "LINE Channel Access Token"
  type        = string
  sensitive   = true
}

variable "line_channel_secret" {
  description = "LINE Channel Secret"
  type        = string
  sensitive   = true
}

# OpenAI API Key
variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}

# ECS Container Image
variable "ecs_image" {
  description = "ECS container image URL"
  type        = string
  default     = "smart-line-bot:latest"
}

# Certificate ARN for HTTPS
variable "certificate_arn" {
  description = "ACM Certificate ARN for HTTPS"
  type        = string
}