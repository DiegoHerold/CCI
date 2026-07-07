from app.infrastructure.clients.base_client import BaseInternalClient


class IdentityClient(BaseInternalClient):
    def __init__(self, base_url: str) -> None:
        super().__init__("identity-service", base_url)
