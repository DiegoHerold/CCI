class S3Storage:
    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool,
    ) -> None:
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import boto3
            from botocore.client import Config

            scheme = "https" if self.secure else "http"
            endpoint = self.endpoint
            if not endpoint.startswith(("http://", "https://")):
                endpoint = f"{scheme}://{endpoint}"
            self._client = boto3.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=Config(signature_version="s3v4"),
                region_name="us-east-1",
            )
        return self._client

    def ensure_bucket(self, bucket: str) -> None:
        buckets = self.client.list_buckets().get("Buckets", [])
        if not any(item.get("Name") == bucket for item in buckets):
            self.client.create_bucket(Bucket=bucket)

    def download_bytes(self, *, bucket: str, key: str) -> bytes:
        response = self.client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    def upload_bytes(
        self,
        *,
        bucket: str,
        key: str,
        content: bytes,
        content_type: str,
        metadata: dict[str, str],
    ) -> None:
        self.ensure_bucket(bucket)
        self.client.put_object(
            Bucket=bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
            Metadata=metadata,
        )
