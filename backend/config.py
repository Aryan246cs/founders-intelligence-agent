from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_secret_key: str = "change-me"

    # Required — nothing works without a database.
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # Required — every agent depends on the LLM.
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    # Required — the research pipeline cannot find competitors without scraping.
    apify_api_token: str

    # Optional integrations: the app degrades to "skip delivery" rather than
    # refusing to boot, so a fresh clone runs with only the three keys above.
    slack_webhook_url: str = ""
    n8n_webhook_base_url: str = "http://localhost:5678/webhook"

    # Comma-separated list of allowed browser origins.
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    rate_limit_per_minute: int = 60

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
