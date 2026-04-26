terraform {
  backend "s3" {
    bucket         = "life-story-agent-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "life-story-terraform-lock"
  }
}
