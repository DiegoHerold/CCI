from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "extraction-service"
    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8130
    database_url: str

    extraction_database_schema: str = "extraction"

    identity_service_url: str = "http://identity-service:8101"
    identity_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    document_service_url: str = "http://document-service:8110"
    document_service_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    template_service_url: str = "http://template-service:8120"
    template_service_timeout_seconds: float = Field(default=5.0, gt=0, le=30)

    temporal_address: str = "temporal:7233"
    temporal_namespace: str = "default"
    extraction_task_queue: str = "extraction-task-queue"
    extraction_workflow_timeout_seconds: int = Field(default=900, gt=0)
    extraction_activity_timeout_seconds: int = Field(default=300, gt=0)

    extraction_max_attempts: int = Field(default=3, ge=1, le=10)
    extraction_retry_initial_interval_seconds: int = Field(default=5, gt=0)
    extraction_retry_backoff_coefficient: float = Field(default=2.0, ge=1)
    extraction_retry_max_interval_seconds: int = Field(default=60, gt=0)

    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_extraction_artifacts: str = "cci-extraction-artifacts"

    pdf_extractor_worker_task_queue: str = "pdf-extractor-task-queue"
    excel_extractor_worker_task_queue: str = "excel-extractor-task-queue"
    pdf_extractor_worker_url: str = "http://pdf-extractor-worker:8131"
    excel_extractor_worker_url: str = "http://excel-extractor-worker:8132"
    extractor_worker_timeout_seconds: float = Field(default=60.0, gt=0, le=300)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
