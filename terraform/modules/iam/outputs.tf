output "service_account_email" {
  description = "Email of the Cloud Run service account"
  value       = google_service_account.cost_optimizer.email
}

output "service_account_id" {
  description = "Fully qualified ID of the service account"
  value       = google_service_account.cost_optimizer.id
}
