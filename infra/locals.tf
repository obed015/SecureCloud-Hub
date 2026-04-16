locals {
  resource_group_name = "rg-${var.project_name}-${var.environment}-${var.location}"

  common_tags = merge(
    var.tags,
    {
      region = var.location
    }
  )
}
