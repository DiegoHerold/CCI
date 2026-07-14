from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "document-service"
    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8110
    database_url: str

    identity_service_url: str = "http://identity-service:8101"
    identity_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    client_service_url: str = "http://client-service:8102"
    client_service_timeout_seconds: float = Field(default=5.0, gt=0, le=30)

    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "cci_minio"
    minio_secret_key: str = "cci_minio_password"
    minio_secure: bool = False
    minio_bucket_documents_original: str = "cci-documents-original"
    minio_bucket_documents_preview: str = "cci-documents-preview"
    minio_presigned_url_expires_seconds: int = Field(default=900, gt=0, le=86400)

    document_max_file_size_mb: int = Field(default=50, gt=0, le=1024)
    document_max_zip_size_mb: int = Field(default=200, gt=0, le=2048)
    document_max_files_per_zip: int = Field(default=100, gt=0, le=1000)
    document_allowed_extensions: str = ".pdf,.xlsx,.xls,.csv,.txt,.docx,.xml,.zip"
    parser_worker_url: str = "http://parser-worker:8121"
    parser_worker_timeout_seconds: float = Field(default=60.0, gt=0, le=600)
    parser_max_file_size_mb: int = Field(default=100, gt=0, le=1024)
    parser_preview_max_json_size_mb: int = Field(default=25, gt=0, le=256)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_extensions(self) -> set[str]:
        return {
            item.strip().lower()
            for item in self.document_allowed_extensions.split(",")
            if item.strip()
        }

    @property
    def max_file_size_bytes(self) -> int:
        return self.document_max_file_size_mb * 1024 * 1024

    @property
    def max_zip_size_bytes(self) -> int:
        return self.document_max_zip_size_mb * 1024 * 1024

    @property
    def parser_max_file_size_bytes(self) -> int:
        return self.parser_max_file_size_mb * 1024 * 1024

    @property
    def parser_preview_max_json_size_bytes(self) -> int:
        return self.parser_preview_max_json_size_mb * 1024 * 1024

    @field_validator("minio_bucket_documents_original", "minio_bucket_documents_preview")
    @classmethod
    def clean_bucket(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("bucket is required")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
