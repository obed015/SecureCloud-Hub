data "azuread_client_config" "current" {}

resource "azuread_application" "securecloud" {
  display_name     = "securecloud-hub-${var.environment}"
  sign_in_audience = "AzureADMyOrg"

  web {
    redirect_uris = [
      "https://placeholder.azurewebsites.net/.auth/login/aad/callback"
    ]

    implicit_grant {
      access_token_issuance_enabled = false
      id_token_issuance_enabled     = true
    }
  }

  tags = [
    "securecloud-hub",
    var.environment
  ]
}

resource "azuread_service_principal" "securecloud" {
  client_id                    = azuread_application.securecloud.client_id
  app_role_assignment_required = false
}
