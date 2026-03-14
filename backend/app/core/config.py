from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Supabase ---
    supabase_url: str = ""
    supabase_key: str = ""

    # --- OpenAI ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # --- AWS ---
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"

    # --- GCP ---
    gcp_project_id: str = ""
    gcp_billing_dataset: str = ""

    # --- App ---
    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    @property
    def demo_mode(self) -> bool:
        """When cloud credentials are missing, run in demo mode with sample data."""
        aws_configured = bool(self.aws_access_key_id and self.aws_secret_access_key)
        gcp_configured = bool(self.gcp_project_id and self.gcp_billing_dataset)
        return not (aws_configured or gcp_configured)

    @property
    def aws_configured(self) -> bool:
        return bool(self.aws_access_key_id and self.aws_secret_access_key)

    @property
    def gcp_configured(self) -> bool:
        return bool(self.gcp_project_id and self.gcp_billing_dataset)

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key)


settings = Settings()
