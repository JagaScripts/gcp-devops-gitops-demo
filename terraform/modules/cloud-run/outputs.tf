output "service_url" {
  description = "Public HTTPS URL of the Cloud Run service."
  value       = google_cloud_run_v2_service.app.uri
}

output "service_name" {
  description = "Name of the Cloud Run service."
  value       = google_cloud_run_v2_service.app.name
}

output "service_account_email" {
  description = "Email of the least-privilege Cloud Run runtime Service Account."
  value       = google_service_account.cloud_run_runtime.email
}

output "artifact_registry_url" {
  description = "Artifact Registry Docker repository URL."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
}
