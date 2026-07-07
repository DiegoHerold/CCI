from app.infrastructure.clients.base_client import BaseInternalClient


class AuditServiceClient(BaseInternalClient):
    def __init__(self, base_url: str) -> None:
        super().__init__("audit-service", base_url)
