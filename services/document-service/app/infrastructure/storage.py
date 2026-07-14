from typing import Protocol

from app.config import Settings
from app.errors import StorageUnavailableError


class StorageClient(Protocol):
    def ensure_bucket(self, bucket: str | None = None) -> None:
        ...

    def upload_bytes(
        self,
        *,
        bucket: str,
        key: str,
        content: bytes,
        content_type: str | None,
        metadata: dict[str, str],
    ) -> None:
        ...

    def presigned_get_url(self, *, bucket: str, key: str) -> str:
        ...

    def download_bytes(self, *, bucket: str, key: str) -> bytes:
        ...


class S3DocumentStorage:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.bucket = settings.minio_bucket_documents_original
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import boto3
                from botocore.client import Config
            except ImportError as exc:
                raise StorageUnavailableError("boto3 is not installed") from exc
            scheme = "https" if self.settings.minio_secure else "http"
            endpoint = self.settings.minio_endpoint
            if not endpoint.startswith(("http://", "https://")):
                endpoint = f"{scheme}://{endpoint}"
            self._client = boto3.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=self.settings.minio_access_key,
                aws_secret_access_key=self.settings.minio_secret_key,
                config=Config(signature_version="s3v4"),
                region_name="us-east-1",
            )
        return self._client

    def ensure_bucket(self, bucket: str | None = None) -> None:
        bucket_name = bucket or self.bucket
        try:
            buckets = self.client.list_buckets().get("Buckets", [])
            if not any(item.get("Name") == bucket_name for item in buckets):
                self.client.create_bucket(Bucket=bucket_name)
        except Exception as exc:
            raise StorageUnavailableError() from exc

    def upload_bytes(
        self,
        *,
        bucket: str,
        key: str,
        content: bytes,
        content_type: str | None,
        metadata: dict[str, str],
    ) -> None:
        try:
            self.ensure_bucket(bucket)
            extra_args = {"Metadata": metadata}
            if content_type:
                extra_args["ContentType"] = content_type
            self.client.put_object(
                Bucket=bucket,
                Key=key,
                Body=content,
                **extra_args,
            )
        except StorageUnavailableError:
            raise
        except Exception as exc:
            raise StorageUnavailableError() from exc

    def presigned_get_url(self, *, bucket: str, key: str) -> str:
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=self.settings.minio_presigned_url_expires_seconds,
            )
        except Exception as exc:
            raise StorageUnavailableError() from exc

    def download_bytes(self, *, bucket: str, key: str) -> bytes:
        try:
            response = self.client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except Exception as exc:
            raise StorageUnavailableError() from exc
