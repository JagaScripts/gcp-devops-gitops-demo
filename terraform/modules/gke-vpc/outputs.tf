output "vpc_id" {
  description = "ID of the custom VPC network."
  value       = google_compute_network.vpc.id
}

output "subnetwork_id" {
  description = "ID of the GKE subnetwork."
  value       = google_compute_subnetwork.gke_subnet.id
}

output "cluster_name" {
  description = "Name of the GKE Autopilot cluster."
  value       = google_container_cluster.autopilot.name
}

output "cluster_endpoint" {
  description = "Control plane endpoint of the GKE Autopilot cluster."
  value       = google_container_cluster.autopilot.endpoint
  sensitive   = true
}
