variable "project_id" {
  description = "Google Cloud project ID where Always Free resources are provisioned."
  type        = string
}

variable "region" {
  description = "GCP region within Cloud Run Always Free Tier 1 (e.g., us-central1, us-east1, us-west1)."
  type        = string
  default     = "us-central1"

  validation {
    condition     = contains(["us-central1", "us-east1", "us-west1"], var.region)
    error_message = "Region must be in Cloud Run Always Free Tier 1 (us-central1, us-east1, or us-west1)."
  }
}

variable "environment" {
  description = "Deployment environment label (dev, staging, prod)."
  type        = string
  default     = "dev"
}

variable "service_name" {
  description = "Name of the Cloud Run service and associated resources."
  type        = string
  default     = "gcp-devops-demo"
}

variable "artifact_registry_repo_id" {
  description = "Repository ID for Docker images in Artifact Registry."
  type        = string
  default     = "devops-demo-images"
}

variable "container_image" {
  description = "Container image URI deployed to Cloud Run."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "container_port" {
  description = "HTTP port exposed by the container."
  type        = number
  default     = 8080
}

variable "allow_unauthenticated" {
  description = "Whether to grant public roles/run.invoker access to the Cloud Run service."
  type        = bool
  default     = true
}

variable "billing_account_id" {
  description = "Optional GCP Billing Account ID to provision the 1 EUR budget alert. Leave empty to skip."
  type        = string
  default     = ""
}

variable "budget_amount_eur" {
  description = "Monthly budget threshold in EUR to enforce zero-cost guardrails."
  type        = number
  default     = 1

  validation {
    condition     = var.budget_amount_eur >= 1 && var.budget_amount_eur <= 5
    error_message = "Budget alert must stay within the strict low-cost guardrail (1 to 5 EUR)."
  }
}
