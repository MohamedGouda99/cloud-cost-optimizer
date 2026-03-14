resource "google_cloud_run_v2_service" "backend" {
  name     = "cost-optimizer-backend"
  location = var.region
  project  = var.project_id

  deletion_protection = false

  template {
    service_account = var.service_account_email

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    containers {
      image = var.image_url

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      # ── Plain-text env vars ──────────────────────────────────
      env {
        name  = "OPENAI_MODEL"
        value = var.openai_model
      }
      env {
        name  = "AWS_REGION"
        value = var.aws_region
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.gcp_project_id
      }
      env {
        name  = "GCP_BILLING_DATASET"
        value = var.gcp_billing_dataset
      }
      env {
        name  = "CORS_ORIGINS"
        value = var.cors_origins
      }

      # ── Secrets from Secret Manager ──────────────────────────
      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = var.secret_openai_api_key_id
            version = "latest"
          }
        }
      }
      env {
        name = "SUPABASE_URL"
        value_source {
          secret_key_ref {
            secret  = var.secret_supabase_url_id
            version = "latest"
          }
        }
      }
      env {
        name = "SUPABASE_KEY"
        value_source {
          secret_key_ref {
            secret  = var.secret_supabase_key_id
            version = "latest"
          }
        }
      }
      env {
        name = "AWS_ACCESS_KEY_ID"
        value_source {
          secret_key_ref {
            secret  = var.secret_aws_access_key_id_id
            version = "latest"
          }
        }
      }
      env {
        name = "AWS_SECRET_ACCESS_KEY"
        value_source {
          secret_key_ref {
            secret  = var.secret_aws_secret_access_key_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Allow unauthenticated access (public API)
resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  project  = var.project_id
  role     = "roles/run.invoker"
  member   = "allUsers"
}
