# Remote state backend configuration for Google Cloud Storage (US Always Free bucket).
# Provide bucket name at init time without hardcoding project-specific identifiers:
#   terraform init -backend-config="bucket=<YOUR_TFSTATE_BUCKET>"
# For local static validation without GCP access:
#   terraform init -backend=false && terraform validate
terraform {
  backend "gcs" {
    prefix = "gcp-devops-gitops-demo/state"
  }
}
