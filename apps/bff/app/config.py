from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "bff"
    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8000
    cors_allowed_origins: str = "http://localhost:3000"
    auth_refresh_cookie_name: str = "cci_refresh_token"
    auth_refresh_cookie_secure: bool = False
    auth_refresh_cookie_samesite: str = Field(
        default="lax", pattern="^(lax|strict)$"
    )
    auth_refresh_cookie_max_age: int = Field(default=604800, gt=0)

    identity_service_url: str = "http://identity-service:8101"
    client_service_url: str = "http://client-service:8102"
    conference_model_service_url: str = "http://conference-model-service:8103"
    schedule_service_url: str = "http://schedule-service:8104"
    document_ingestion_service_url: str = "http://document-ingestion-service:8110"
    document_classification_service_url: str = "http://document-classification-service:8111"
    variable_registry_service_url: str = "http://variable-registry-service:8120"
    rule_service_url: str = "http://rule-service:8130"
    execution_control_service_url: str = "http://execution-control-service:8140"
    result_service_url: str = "http://result-service:8141"
    audit_service_url: str = "http://audit-service:8150"
    report_service_url: str = "http://report-service:8160"
    log_service_url: str = "http://log-service:8170"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @model_validator(mode="after")
    def require_secure_cookie_in_production(self) -> "Settings":
        if (
            self.app_env.casefold() == "production"
            and not self.auth_refresh_cookie_secure
        ):
            raise ValueError("refresh cookie must be Secure in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
