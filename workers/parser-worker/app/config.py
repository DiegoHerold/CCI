from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "parser-worker"
    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8121
    parser_worker_version: str = "1.0.0"
    parser_worker_concurrency: int = Field(default=2, ge=1, le=16)
    parser_max_file_size_mb: int = Field(default=100, gt=0, le=1024)
    parser_preview_max_json_size_mb: int = Field(default=25, gt=0, le=256)

    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "cci_minio"
    minio_secret_key: str = "cci_minio_password"
    minio_secure: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def parser_max_file_size_bytes(self) -> int:
        return self.parser_max_file_size_mb * 1024 * 1024

    @property
    def parser_preview_max_json_size_bytes(self) -> int:
        return self.parser_preview_max_json_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
