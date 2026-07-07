from app.infrastructure.clients.base_client import BaseInternalClient


class DocumentClassificationClient(BaseInternalClient):
    def __init__(self, base_url: str) -> None:
        super().__init__("document-classification-service", base_url)
