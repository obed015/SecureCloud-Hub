resource "azurerm_role_assignment" "func_blob_contributor" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azapi_resource.flex_function_app.output.identity.principalId
}

resource "azurerm_role_assignment" "func_blob_reader" {
  scope                = azurerm_storage_container.safe_files.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azapi_resource.flex_function_app.output.identity.principalId
}

resource "azurerm_role_assignment" "func_blob_delegator" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Delegator"
  principal_id         = azapi_resource.flex_function_app.output.identity.principalId
}