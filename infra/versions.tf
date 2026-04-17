terraform {
  required_version = ">= 1.7.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.26"
    }

    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.2"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }

    azapi = {
      source  = "Azure/azapi"
      version = "~> 2.3"
    }
  }
}