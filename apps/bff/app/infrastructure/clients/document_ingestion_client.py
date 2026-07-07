from app.infrastructure.clients.base_client import BaseInternalClient


class DocumentIngestionClient(BaseInternalClient):
    def __init__(self, base_url: str) -> None:
        super().__init__("document-ingestion-service", base_url)
