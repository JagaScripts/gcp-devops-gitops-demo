locals {
  common_labels = {
    app         = var.service_name
    environment = var.environment
    managed_by  = "terraform"
    tier        = "always-free"
  }
}

# Dedicated least-privilege runtime Service Account for Cloud Run
resource "google_service_account" "cloud_run_runtime" {
  project      = var.project_id
  account_id   = "${var.service_name}-sa"
  display_name = "Cloud Run runtime SA for ${var.service_name}"
  description  = "Least-privilege runtime identity for Cloud Run service ${var.service_name}."
}

# Minimal project-level permission: emit structured logs to Cloud Logging only
resource "google_project_iam_member" "logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloud_run_runtime.email}"
}

# Artifact Registry Docker repository (Always Free: 0.5 GB storage/month)
resource "google_artifact_registry_repository" "docker_repo" {
  project       = var.project_id
  location      = var.region
  repository_id = var.artifact_registry_repo_id
  description   = "Docker images for ${var.service_name} (${var.environment})"
  format        = "DOCKER"
  labels        = local.common_labels

  cleanup_policies {
    id     = "keep-recent-versions"
    action = "KEEP"

    most_recent_versions {
      keep_count = 3
    }
  }
}

# Scoped read-only access to the specific Artifact Registry repository
resource "google_artifact_registry_repository_iam_member" "runtime_reader" {
  project    = var.project_id
  location   = google_artifact_registry_repository.docker_repo.location
  repository = google_artifact_registry_repository.docker_repo.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.cloud_run_runtime.email}"
}

# Cloud Run v2 Service configured strictly for Always Free scale-to-zero
resource "google_cloud_run_v2_service" "app" {
  project  = var.project_id
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  labels   = local.common_labels

  template {
    service_account                  = google_service_account.cloud_run_runtime.email
    max_instance_request_concurrency = 80
    timeout                          = "60s"

    scaling {
      min_instance_count = 0
      max_instance_count = var.max_instances
    }

    containers {
      image = var.container_image

      ports {
        container_port = var.container_port
      }

      env {
        name  = "APP_ENV"
        value = var.environment
      }

      env {
        name  = "SERVICE_NAME"
        value = var.service_name
      }

      resources {
        cpu_idle = true
        limits = {
          cpu    = "1"
          memory = "256Mi"
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = var.container_port
        }
        initial_delay_seconds = 2
        period_seconds        = 5
        timeout_seconds       = 2
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = var.container_port
        }
        period_seconds    = 15
        timeout_seconds   = 2
        failure_threshold = 3
      }
    }
  }

  depends_on = [
    google_artifact_registry_repository_iam_member.runtime_reader,
    google_project_iam_member.logging_writer
  ]
}

resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  count = var.allow_unauthenticated ? 1 : 0

  project  = google_cloud_run_v2_service.app.project
  location = google_cloud_run_v2_service.app.location
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
