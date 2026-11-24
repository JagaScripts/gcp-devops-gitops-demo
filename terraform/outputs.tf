output "cloud_run_url" {
  description = "Public HTTPS URL of the deployed Cloud Run service."
  value       = module.cloud_run.service_url
}

output "cloud_run_service_account_email" {
  description = "Least-privilege runtime Service Account email for Cloud Run."
  value       = module.cloud_run.service_account_email
}

output "artifact_registry_repository_url" {
  description = "Docker push/pull URL for the Artifact Registry repository."
  value       = module.cloud_run.artifact_registry_url
}
