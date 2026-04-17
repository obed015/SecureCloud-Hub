resource "azurerm_eventgrid_system_topic" "blob_events" {
  name                = "evgt-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  source_resource_id  = azurerm_storage_account.main.id
  topic_type          = "Microsoft.Storage.StorageAccounts"

  tags = local.common_tags
}

resource "azurerm_eventgrid_system_topic_event_subscription" "scan_trigger" {
  name                = "sub-scan-on-upload"
  system_topic        = azurerm_eventgrid_system_topic.blob_events.name
  resource_group_name = azurerm_resource_group.main.name

  included_event_types = ["Microsoft.Storage.BlobCreated"]

  subject_filter {
    subject_begins_with = "/blobServices/default/containers/incoming-raw/"
    case_sensitive      = false
  }

  azure_function_endpoint {
    function_id = "${azapi_resource.flex_function_app.id}/functions/scan_function"

    max_events_per_batch              = 1
    preferred_batch_size_in_kilobytes = 64
  }

  retry_policy {
    max_delivery_attempts = 30
    event_time_to_live    = 1440
  }

  depends_on = [
    azapi_resource.flex_function_app
  ]
}