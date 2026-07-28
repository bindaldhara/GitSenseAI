from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GitSense AI"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:5173"
    postgres_db: str = "gitsense"
    postgres_user: str = "gitsense"
    postgres_password: str = "gitsense"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    redis_url: str = "redis://redis:6379/0"
    qdrant_url: str = "http://qdrant:6333"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
