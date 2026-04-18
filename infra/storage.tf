# ============================================================
# storage.tf
# Storage account + private containers + lifecycle rules
#
# Security decisions:
# - public_network_access_enabled left on for MVP
# - allow_nested_items_to_be_public = false prevents public blob access
# - container_access_type = "private" blocks anonymous reads
# - versioning + soft delete protect against mistakes
# - lifecycle policies control cost and cleanup
# - CORS allows the authenticated frontend hosted on the Function App
#   to upload directly to Blob Storage using short-lived SAS URLs
# ============================================================

resource "azurerm_storage_account" "main" {
  name                     = "st${var.project_name}${var.environment}001"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  # Security baseline
  allow_nested_items_to_be_public = false
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  shared_access_key_enabled       = true

  blob_properties {
    versioning_enabled = true

    delete_retention_policy {
      days = 30
    }

    container_delete_retention_policy {
      days = 30
    }

    cors_rule {
      allowed_origins = [
        "https://${azapi_resource.flex_function_app.output.properties.defaultHostName}"
      ]
      allowed_methods = ["GET", "PUT", "OPTIONS"]
      allowed_headers = ["*"]
      exposed_headers = ["*"]
      max_age_in_seconds = 3600
    }
  }

  tags = local.common_tags
}

resource "azurerm_storage_container" "incoming_raw" {
  name                  = "incoming-raw"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "safe_files" {
  name                  = "safe-files"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "quarantine" {
  name                  = "quarantine"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "function_packages" {
  name                  = "function-packages"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_storage_management_policy" "lifecycle" {
  storage_account_id = azurerm_storage_account.main.id

  rule {
    name    = "incoming-raw-cleanup"
    enabled = true

    filters {
      prefix_match = ["incoming-raw/"]
      blob_types   = ["blockBlob"]
    }

    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = 2
      }
    }
  }

  rule {
    name    = "safe-files-tiering"
    enabled = true

    filters {
      prefix_match = ["safe-files/"]
      blob_types   = ["blockBlob"]
    }

    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than = 30
        delete_after_days_since_modification_greater_than       = 365
      }
    }
  }

  rule {
    name    = "quarantine-cleanup"
    enabled = true

    filters {
      prefix_match = ["quarantine/"]
      blob_types   = ["blockBlob"]
    }

    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = 7
      }
    }
  }
}