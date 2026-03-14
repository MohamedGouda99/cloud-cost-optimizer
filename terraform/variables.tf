variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run deployment"
  type        = string
  default     = "us-central1"
}

variable "backend_image_url" {
  description = "Container image URL for the backend (e.g. gcr.io/PROJECT/cost-optimizer-backend:latest)"
  type        = string
}

# ─── Application Secrets ────────────────────────────────────────

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "openai_model" {
  description = "OpenAI model name"
  type        = string
  default     = "gpt-4o"
}

variable "supabase_url" {
  description = "Supabase project URL"
  type        = string
  sensitive   = true
}

variable "supabase_key" {
  description = "Supabase anon/service key"
  type        = string
  sensitive   = true
}

variable "aws_access_key_id" {
  description = "AWS access key for Cost Explorer"
  type        = string
  sensitive   = true
}

variable "aws_secret_access_key" {
  description = "AWS secret access key"
  type        = string
  sensitive   = true
}

variable "aws_region" {
  description = "AWS region for Cost Explorer API"
  type        = string
  default     = "us-east-1"
}

variable "gcp_billing_dataset" {
  description = "BigQuery dataset for GCP billing export (format: dataset.table)"
  type        = string
  default     = "billing_export.gcp_billing_export_v1"
}

variable "cors_origins" {
  description = "Comma-separated list of allowed CORS origins"
  type        = string
  default     = "*"
}
