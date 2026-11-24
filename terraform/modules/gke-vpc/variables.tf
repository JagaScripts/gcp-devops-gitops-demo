variable "project_id" {
  description = "Google Cloud project ID (static validation only; never apply in Always Free mode)."
  type        = string
}

variable "region" {
  description = "Google Cloud region for the VPC subnetwork and GKE Autopilot cluster."
  type        = string
  default     = "europe-southwest1"
}

variable "network_name" {
  description = "Name of the custom VPC network."
  type        = string
  default     = "devops-demo-vpc"
}

variable "subnet_name" {
  description = "Name of the primary subnetwork for GKE Autopilot."
  type        = string
  default     = "devops-demo-gke-subnet"
}

variable "subnet_cidr" {
  description = "Primary IPv4 CIDR range for GKE nodes."
  type        = string
  default     = "10.10.0.0/20"
}

variable "pods_range_name" {
  description = "Secondary IP range name allocated to Kubernetes Pods."
  type        = string
  default     = "gke-pods-range"
}

variable "pods_cidr" {
  description = "Secondary IPv4 CIDR range for Kubernetes Pods."
  type        = string
  default     = "10.20.0.0/16"
}

variable "services_range_name" {
  description = "Secondary IP range name allocated to Kubernetes Services."
  type        = string
  default     = "gke-services-range"
}

variable "services_cidr" {
  description = "Secondary IPv4 CIDR range for Kubernetes Services."
  type        = string
  default     = "10.30.0.0/20"
}

variable "cluster_name" {
  description = "Name of the GKE Autopilot cluster."
  type        = string
  default     = "devops-demo-autopilot"
}

variable "release_channel" {
  description = "GKE release channel (RAPID, REGULAR, or STABLE)."
  type        = string
  default     = "REGULAR"

  validation {
    condition     = contains(["RAPID", "REGULAR", "STABLE"], var.release_channel)
    error_message = "release_channel must be RAPID, REGULAR, or STABLE."
  }
}

variable "master_ipv4_cidr_block" {
  description = "Private IPv4 CIDR block for the GKE control plane."
  type        = string
  default     = "172.16.0.0/28"
}

variable "deletion_protection" {
  description = "Enable or disable cluster deletion protection."
  type        = bool
  default     = false
}
