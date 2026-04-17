terraform {
  backend "azurerm" {
    resource_group_name  = "rg-securecloud-dev-ukwest"
    storage_account_name = "stsecureclouddev001"
    container_name       = "tfstate"
    key                  = "securecloud.tfstate"
    use_azuread_auth     = true
  }
}