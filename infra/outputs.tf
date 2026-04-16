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
