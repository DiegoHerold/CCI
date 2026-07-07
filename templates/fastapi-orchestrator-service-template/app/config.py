from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "{{SERVICE_NAME}}"
    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8000

    database_url: str | None = None
    redis_url: str | None = None
    rabbitmq_url: str | None = None
    temporal_address: str | None = None
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
