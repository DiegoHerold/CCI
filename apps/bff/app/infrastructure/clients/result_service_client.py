from app.infrastructure.clients.base_client import BaseInternalClient


class ResultServiceClient(BaseInternalClient):
    def __init__(self, base_url: str) -> None:
        super().__init__("result-service", base_url)
