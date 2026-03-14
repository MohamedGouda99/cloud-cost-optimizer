resource "google_service_account" "cost_optimizer" {
  account_id   = "cost-optimizer-sa"
  display_name = "Cost Optimizer Cloud Run Service Account"
  project      = var.project_id
}

locals {
  roles = [
    "roles/bigquery.dataViewer",
    "roles/bigquery.jobUser",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ]
}

resource "google_project_iam_member" "sa_roles" {
  for_each = toset(local.roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cost_optimizer.email}"
}
