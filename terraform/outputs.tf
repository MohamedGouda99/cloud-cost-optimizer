output "backend_url" {
  description = "Cloud Run backend service URL"
  value       = module.cloud_run.service_url
}

output "service_account_email" {
  description = "Service account used by Cloud Run"
  value       = module.iam.service_account_email
}

output "enabled_apis" {
  description = "List of enabled GCP APIs"
  value       = module.apis.enabled_apis
}
