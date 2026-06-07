from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KOL AI Assistant Service"
    app_env: str = "development"
    app_port: int = 8001
    database_url: str = "postgresql+asyncpg://kol_user:kol_secret@localhost:5432/kol_booking"
    spring_backend_base_url: str = "http://localhost:8080"
    spring_backend_internal_token: str | None = None
    llm_provider: str = "openai"
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_max_retries: int = 2
    request_timeout_seconds: int = 10
    backend_request_retries: int = 2
    max_recommendation_candidates: int = 50
    default_top_k: int = 5

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
