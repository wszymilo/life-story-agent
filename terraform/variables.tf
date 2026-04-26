variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-west-1"
}

variable "environment" {
  description = "Environment name (production, staging, development)"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "life-story-agent"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_a_cidr" {
  description = "CIDR for public subnet A"
  type        = string
  default     = "10.0.1.0/24"
}

variable "public_subnet_b_cidr" {
  description = "CIDR for public subnet B"
  type        = string
  default     = "10.0.2.0/24"
}

variable "private_subnet_a_cidr" {
  description = "CIDR for private subnet A (Aurora, ECS)"
  type        = string
  default     = "10.0.11.0/24"
}

variable "private_subnet_b_cidr" {
  description = "CIDR for private subnet B (Aurora, ECS)"
  type        = string
  default     = "10.0.12.0/24"
}

variable "availability_zones" {
  description = "Availability zones for subnets"
  type        = list(string)
  default     = ["eu-west-1a", "eu-west-1b"]
}

variable "db_name" {
  description = "Aurora database name"
  type        = string
  default     = "life_story_agent"
}

variable "db_username" {
  description = "Master username for Aurora"
  type        = string
  default     = "dbadmin"
}

variable "db_min_capacity" {
  description = "Minimum Aurora Serverless v2 capacity units"
  type        = number
  default     = 0
}

variable "db_max_capacity" {
  description = "Maximum Aurora Serverless v2 capacity units"
  type        = number
  default     = 4
}

variable "db_auto_pause" {
  description = "Enable Aurora Serverless auto-pause"
  type        = number
  default     = 300
}

variable "ecs_task_cpu" {
  description = "ECS task CPU units (256 = 0.25 vCPU, 512 = 0.5 vCPU)"
  type        = number
  default     = 512
}

variable "ecs_task_memory" {
  description = "ECS task memory in MB"
  type        = number
  default     = 1024
}

variable "cognito_totp_issuer" {
  description = "Issuer string for Cognito TOTP (used in Google Authenticator)"
  type        = string
  default     = "Life Story Agent"
}

variable "allowed_cors_origins" {
  description = "Comma-separated list of allowed CORS origins"
  type        = string
  default     = ""
}

variable "frontend_bucket_name" {
  description = "S3 bucket name for frontend static files"
  type        = string
  default     = "life-story-agent-frontend"
}

variable "audio_bucket_name" {
  description = "S3 bucket name for audio recordings"
  type        = string
  default     = "life-story-agent-audio"
}

variable "terraform_state_bucket" {
  description = "S3 bucket name for Terraform state"
  type        = string
  default     = "life-story-agent-terraform-state"
}
