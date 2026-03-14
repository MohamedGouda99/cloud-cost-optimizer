output "openai_api_key_secret_id" {
  description = "Secret Manager secret ID for OpenAI API key"
  value       = google_secret_manager_secret.secrets["openai-api-key"].secret_id
}

output "supabase_url_secret_id" {
  description = "Secret Manager secret ID for Supabase URL"
  value       = google_secret_manager_secret.secrets["supabase-url"].secret_id
}

output "supabase_key_secret_id" {
  description = "Secret Manager secret ID for Supabase key"
  value       = google_secret_manager_secret.secrets["supabase-key"].secret_id
}

output "aws_access_key_id_secret_id" {
  description = "Secret Manager secret ID for AWS access key ID"
  value       = google_secret_manager_secret.secrets["aws-access-key-id"].secret_id
}

output "aws_secret_access_key_secret_id" {
  description = "Secret Manager secret ID for AWS secret access key"
  value       = google_secret_manager_secret.secrets["aws-secret-access-key"].secret_id
}
