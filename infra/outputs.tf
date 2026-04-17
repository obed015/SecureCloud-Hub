output "resource_group_name" {
  description = "Name of the deployed resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "Azure region the resource group is deployed to"
  value       = azurerm_resource_group.main.location
}

output "subscription_id" {
  description = "Active Azure subscription ID"
  value       = data.azurerm_client_config.current.subscription_id
}

output "tenant_id" {
  description = "Active Microsoft Entra tenant ID"
  value       = data.azurerm_client_config.current.tenant_id
}

output "storage_account_name" {
  description = "Storage account name"
  value       = azurerm_storage_account.main.name
}

output "storage_account_id" {
  description = "Storage account resource ID"
  value       = azurerm_storage_account.main.id
}

output "function_packages_container_name" {
  description = "Container used for Flex Function App deployment packages"
  value       = azurerm_storage_container.function_packages.name
}

output "entra_app_client_id" {
  description = "Client ID of the Entra ID app registration"
  value       = azuread_application.securecloud.client_id
}

output "entra_service_principal_id" {
  description = "Object ID of the Entra service principal"
  value       = azuread_service_principal.securecloud.object_id
}

output "function_app_name" {
  description = "Function App name"
  value       = azapi_resource.flex_function_app.name
}

output "function_app_hostname" {
  description = "Function App hostname"
  value       = azapi_resource.flex_function_app.output.properties.defaultHostName
}

output "function_app_principal_id" {
  description = "Function App managed identity principal ID"
  value       = azapi_resource.flex_function_app.output.identity.principalId
}

output "app_insights_connection_string" {
  description = "Application Insights connection string"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}