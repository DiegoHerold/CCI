from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    worker_name: str = "{{WORKER_NAME}}"
    app_env: str = "development"
    log_level: str = "INFO"

    rabbitmq_url: str | None = None
    temporal_address: str | None = None
    minio_endpoint: str | None = None
    database_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
