variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "ukwest"
}

variable "environment" {
  description = "Environment name used in resource naming"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Short project identifier used in resource names"
  type        = string
  default     = "securecloud"
}

variable "tags" {
  description = "Tags applied to every resource for governance and cost tracking"
  type        = map(string)
  default = {
    project     = "securecloud-hub"
    environment = "dev"
    owner       = "obed-owusu"
    managed_by  = "terraform"
    portfolio   = "true"
  }
}
