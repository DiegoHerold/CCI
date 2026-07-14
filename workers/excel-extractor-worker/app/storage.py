import json


class S3Storage:
    def __init__(self, *, endpoint: str, access_key: str, secret_key: str, secure: bool) -> None:
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

    def load_json(self, *, bucket: str, key: str, max_size_bytes: int) -> dict:
        response = self.client.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read(max_size_bytes + 1)
        if len(content) > max_size_bytes:
            raise ValueError("preview JSON exceeds extractor size limit")
        return json.loads(content.decode("utf-8"))
