locals {
  create_scan_role_assignments     = var.scan_function_principal_id != ""
  create_download_role_assignments = var.download_function_principal_id != ""
}

resource "azurerm_role_assignment" "scan_function_blob_contributor" {
  count                = local.create_scan_role_assignments ? 1 : 0
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.scan_function_principal_id
}

resource "azurerm_role_assignment" "download_function_blob_reader" {
  count                = local.create_download_role_assignments ? 1 : 0
  scope                = azurerm_storage_container.safe_files.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = var.download_function_principal_id
}

resource "azurerm_role_assignment" "download_function_delegation" {
  count                = local.create_download_role_assignments ? 1 : 0
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Delegator"
  principal_id         = var.download_function_principal_id
}