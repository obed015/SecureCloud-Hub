resource "random_string" "func_suffix" {
  length  = 5
  upper   = false
  special = false
  numeric = true
}

locals {
  function_app_name  = "func-${var.project_name}-${var.environment}-${random_string.func_suffix.result}"
  function_plan_name = "asp-${var.project_name}-${var.environment}-${random_string.func_suffix.result}"
}

resource "azurerm_service_plan" "flex" {
  name                = local.function_plan_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "FC1"

  tags = local.common_tags
}

resource "azapi_resource" "flex_function_app" {
  type      = "Microsoft.Web/sites@2023-12-01"
  name      = local.function_app_name
  location  = azurerm_resource_group.main.location
  parent_id = azurerm_resource_group.main.id

  identity {
    type = "SystemAssigned"
  }

  body = {
    kind = "functionapp,linux"
    properties = {
      serverFarmId        = azurerm_service_plan.flex.id
      httpsOnly           = true
      publicNetworkAccess = "Enabled"

      siteConfig = {
        appSettings = [
          {
            name  = "STORAGE_ACCOUNT_URL"
            value = "https://${azurerm_storage_account.main.name}.blob.core.windows.net"
          },
          {
            name  = "INCOMING_CONTAINER"
            value = azurerm_storage_container.incoming_raw.name
          },
          {
            name  = "SAFE_CONTAINER"
            value = azurerm_storage_container.safe_files.name
          },
          {
            name  = "QUARANTINE_CONTAINER"
            value = azurerm_storage_container.quarantine.name
          },
          {
            name  = "FUNCTION_PACKAGES_CONTAINER"
            value = azurerm_storage_container.function_packages.name
          },
          {
            name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
            value = azurerm_application_insights.main.connection_string
          },
          {
            name  = "AzureWebJobsStorage__accountName"
            value = azurerm_storage_account.main.name
          }
        ]
      }

      functionAppConfig = {
        deployment = {
          storage = {
            type  = "blobContainer"
            value = "https://${azurerm_storage_account.main.name}.blob.core.windows.net/${azurerm_storage_container.function_packages.name}"
            authentication = {
              type = "SystemAssignedIdentity"
            }
          }
        }

        runtime = {
          name    = "python"
          version = "3.11"
        }

        scaleAndConcurrency = {
          instanceMemoryMB     = 2048
          maximumInstanceCount = 40
        }
      }
    }
  }

  response_export_values = [
    "name",
    "properties.defaultHostName",
    "identity.principalId"
  ]

  tags = local.common_tags
}

resource "azapi_update_resource" "flex_function_auth" {
  type        = "Microsoft.Web/sites/config@2023-12-01"
  resource_id = "${azapi_resource.flex_function_app.id}/config/authsettingsV2"

  body = {
    properties = {
      platform = {
        enabled = true
      }
      globalValidation = {
        unauthenticatedClientAction = "RedirectToLoginPage"
        excludedPaths = [
          "/runtime/webhooks/eventgrid"
        ]
      }
      identityProviders = {
        azureActiveDirectory = {
          enabled = true
          registration = {
            clientId     = azuread_application.securecloud.client_id
            openIdIssuer = "https://login.microsoftonline.com/${data.azurerm_client_config.current.tenant_id}/v2.0"
          }
        }
      }
      login = {
        tokenStore = {
          enabled = true
        }
      }
    }
  }

  depends_on = [azapi_resource.flex_function_app]
}