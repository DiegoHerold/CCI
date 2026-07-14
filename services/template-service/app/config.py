from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "template-service"
    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8120
    database_url: str

    identity_service_url: str = "http://identity-service:8101"
    identity_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    document_service_url: str = "http://document-service:8110"
    document_service_timeout_seconds: float = Field(default=5.0, gt=0, le=30)

    template_database_schema: str = "template"
    template_max_selection_payload_kb: int = Field(default=256, gt=0, le=4096)
    template_max_rule_config_kb: int = Field(default=128, gt=0, le=4096)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def max_selection_payload_bytes(self) -> int:
        return self.template_max_selection_payload_kb * 1024

    @property
    def max_rule_config_bytes(self) -> int:
        return self.template_max_rule_config_kb * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
