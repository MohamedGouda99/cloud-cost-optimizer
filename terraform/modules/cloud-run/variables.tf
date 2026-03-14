variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "image_url" {
  description = "Container image URL for the backend"
  type        = string
}

variable "service_account_email" {
  description = "Service account email for Cloud Run"
  type        = string
}

# ─── Secret Manager references ──────────────────────────────────

variable "secret_openai_api_key_id" {
  description = "Secret Manager secret ID for OpenAI API key"
  type        = string
}

variable "secret_supabase_url_id" {
  description = "Secret Manager secret ID for Supabase URL"
  type        = string
}

variable "secret_supabase_key_id" {
  description = "Secret Manager secret ID for Supabase key"
  type        = string
}

variable "secret_aws_access_key_id_id" {
  description = "Secret Manager secret ID for AWS access key ID"
  type        = string
}

variable "secret_aws_secret_access_key_id" {
  description = "Secret Manager secret ID for AWS secret access key"
  type        = string
}

# ─── Plain-text env vars ────────────────────────────────────────

variable "openai_model" {
  description = "OpenAI model name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "gcp_project_id" {
  description = "GCP project ID (passed as env var)"
  type        = string
}

variable "gcp_billing_dataset" {
  description = "BigQuery billing dataset"
  type        = string
}

variable "cors_origins" {
  description = "Allowed CORS origins"
  type        = string
}
