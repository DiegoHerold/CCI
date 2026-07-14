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
    template_match_min_confidence: float = Field(default=0.75, ge=0, le=1)
    template_match_auto_accept_confidence: float = Field(default=0.90, ge=0, le=1)
    template_match_auto_confirm_threshold: float = Field(default=0.95, ge=0, le=1)
    template_match_require_confirmation: bool = True
    template_match_ambiguity_delta: float = Field(default=0.08, ge=0, le=1)
    template_match_max_candidates: int = Field(default=10, ge=1, le=100)
    template_profile_text_sample_limit: int = Field(default=5000, ge=100, le=50000)
    template_profile_max_keywords: int = Field(default=200, ge=1, le=1000)

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
