from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_secret_key: str = "change-me"

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    groq_api_key: str
    groq_model: str = "llama3-70b-8192"

    apify_api_token: str

    slack_webhook_url: str

    n8n_webhook_base_url: str = "http://localhost:5678/webhook"

    redis_url: str = "redis://localhost:6379/0"

    rate_limit_per_minute: int = 60


settings = Settings()
