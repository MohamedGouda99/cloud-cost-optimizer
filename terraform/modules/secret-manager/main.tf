locals {
  secrets = {
    openai-api-key        = var.openai_api_key
    supabase-url          = var.supabase_url
    supabase-key          = var.supabase_key
    aws-access-key-id     = var.aws_access_key_id
    aws-secret-access-key = var.aws_secret_access_key
  }
}

resource "google_secret_manager_secret" "secrets" {
  for_each  = local.secrets
  secret_id = "cost-optimizer-${each.key}"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "versions" {
  for_each    = local.secrets
  secret      = google_secret_manager_secret.secrets[each.key].id
  secret_data = each.value
}

resource "google_secret_manager_secret_iam_member" "accessor" {
  for_each  = local.secrets
  secret_id = google_secret_manager_secret.secrets[each.key].secret_id
  project   = var.project_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}
