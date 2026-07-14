import hashlib
import json
from typing import Any

from app.config import Settings
from app.errors import StorageUnavailableError


class ArtifactStorage:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_key(self, *, client_id: str, competence_id: str, document_id: str, job_id: str) -> str:
        return (
            f"clients/{client_id}/competences/{competence_id}/documents/{document_id}"
            f"/extractions/{job_id}/artifact.json"
        )

    def save_json(self, key: str, payload: dict[str, Any]) -> tuple[str, str]:
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        content_hash = hashlib.sha256(encoded).hexdigest()
        bucket = self.settings.minio_bucket_extraction_artifacts
        try:
            self._upload_bytes(bucket, key, encoded)
        except Exception as exc:
            raise StorageUnavailableError() from exc
        return bucket, content_hash

    def _upload_bytes(self, bucket: str, key: str, content: bytes) -> None:
        try:
            import boto3
            from botocore.client import Config
        except ImportError as exc:
            raise StorageUnavailableError("boto3 is not installed") from exc
        scheme = "https" if self.settings.minio_secure else "http"
        endpoint = self.settings.minio_endpoint
        if not endpoint.startswith(("http://", "https://")):
            endpoint = f"{scheme}://{endpoint}"
        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=self.settings.minio_access_key,
            aws_secret_access_key=self.settings.minio_secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        buckets = client.list_buckets().get("Buckets", [])
        if not any(item.get("Name") == bucket for item in buckets):
            client.create_bucket(Bucket=bucket)
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=content,
            ContentType="application/json",
            Metadata={"sha256": hashlib.sha256(content).hexdigest()},
        )
