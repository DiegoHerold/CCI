from app.infrastructure.clients.base_client import BaseInternalClient


class LogServiceClient(BaseInternalClient):
    def __init__(self, base_url: str) -> None:
        super().__init__("log-service", base_url)
