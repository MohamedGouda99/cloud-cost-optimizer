terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "cost-optimizer-tf-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ─── Enable Required APIs ───────────────────────────────────────
module "apis" {
  source     = "./modules/apis"
  project_id = var.project_id
}

# ─── IAM: Service Account & Roles ──────────────────────────────
module "iam" {
  source     = "./modules/iam"
  project_id = var.project_id

  depends_on = [module.apis]
}

# ─── Secret Manager: Store Application Secrets ─────────────────
module "secret_manager" {
  source     = "./modules/secret-manager"
  project_id = var.project_id

  openai_api_key        = var.openai_api_key
  supabase_url          = var.supabase_url
  supabase_key          = var.supabase_key
  aws_access_key_id     = var.aws_access_key_id
  aws_secret_access_key = var.aws_secret_access_key

  service_account_email = module.iam.service_account_email

  depends_on = [module.apis]
}

# ─── Cloud Run: Deploy Backend API ─────────────────────────────
module "cloud_run" {
  source     = "./modules/cloud-run"
  project_id = var.project_id
  region     = var.region

  image_url             = var.backend_image_url
  service_account_email = module.iam.service_account_email

  secret_openai_api_key_id        = module.secret_manager.openai_api_key_secret_id
  secret_supabase_url_id          = module.secret_manager.supabase_url_secret_id
  secret_supabase_key_id          = module.secret_manager.supabase_key_secret_id
  secret_aws_access_key_id_id     = module.secret_manager.aws_access_key_id_secret_id
  secret_aws_secret_access_key_id = module.secret_manager.aws_secret_access_key_secret_id

  openai_model       = var.openai_model
  aws_region         = var.aws_region
  gcp_project_id     = var.project_id
  gcp_billing_dataset = var.gcp_billing_dataset
  cors_origins       = var.cors_origins

  depends_on = [module.iam, module.secret_manager]
}
