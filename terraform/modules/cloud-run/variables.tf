variable "project_id" {
  description = "Google Cloud project ID."
  type        = string
}

variable "region" {
  description = "Google Cloud region for Artifact Registry and Cloud Run."
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment label."
  type        = string
  default     = "dev"
}

variable "service_name" {
  description = "Name of the Cloud Run v2 service."
  type        = string
  default     = "gcp-devops-demo"
}

variable "artifact_registry_repo_id" {
  description = "Repository ID in Artifact Registry for container images."
  type        = string
  default     = "devops-demo-images"
}

variable "container_image" {
  description = "Container image URI to deploy on Cloud Run."
  type        = string
}

variable "container_port" {
  description = "Port exposed by the container."
  type        = number
  default     = 8080
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances (kept low for Always Free)."
  type        = number
  default     = 2

  validation {
    condition     = var.max_instances >= 1 && var.max_instances <= 5
    error_message = "max_instances must be between 1 and 5 to protect Always Free quotas."
  }
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated HTTP requests to Cloud Run."
  type        = bool
  default     = true
}
