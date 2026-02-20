"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    # Google
    google_credentials_path: str = "credentials/credentials.json"
    google_token_path: str = "credentials/token.json"

    # Cache
    cache_ttl_seconds: int = 300  # 5 minutes

    # Defaults
    default_since_hours: int = 48
    log_level: str = "INFO"

    # Google API scopes (not from env)
    google_scopes: list[str] = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/documents.readonly",
    ]

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )
