provider "google" {
  project = var.project_id
  region  = var.region
}

# Active Always Free infrastructure: IAM (least privilege), Artifact Registry and Cloud Run.
# NOTE: The GKE Autopilot + VPC module (./modules/gke-vpc) is intentionally NOT instantiated
# in this root stack so no billable cluster or network resources are ever provisioned online.
module "cloud_run" {
  source = "./modules/cloud-run"

  project_id                = var.project_id
  region                    = var.region
  environment               = var.environment
  service_name              = var.service_name
  artifact_registry_repo_id = var.artifact_registry_repo_id
  container_image           = var.container_image
  container_port            = var.container_port
  allow_unauthenticated     = var.allow_unauthenticated
}

resource "google_billing_budget" "zero_cost_guardrail" {
  count = var.billing_account_id != "" ? 1 : 0

  billing_account = var.billing_account_id
  display_name    = "${var.service_name}-budget-${var.budget_amount_eur}eur"

  budget_filter {
    projects = ["projects/${var.project_id}"]
  }

  amount {
    specified_amount {
      currency_code = "EUR"
      units         = tostring(var.budget_amount_eur)
    }
  }

  threshold_rules {
    threshold_percent = 0.5
  }

  threshold_rules {
    threshold_percent = 0.8
  }

  threshold_rules {
    threshold_percent = 1.0
  }
}
