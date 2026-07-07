from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "client-service"
    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8102
    database_url: str
    identity_service_url: str = "http://identity-service:8101"
    identity_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    default_competence_folder_pattern: str = "{{YYYY}}/{{MM}}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

