from app.infrastructure.clients.base_client import BaseInternalClient


class ClientServiceClient(BaseInternalClient):
    def __init__(self, base_url: str) -> None:
        super().__init__("client-service", base_url)
