from app.infrastructure.clients.base_client import BaseInternalClient


class ConferenceModelClient(BaseInternalClient):
    def __init__(self, base_url: str) -> None:
        super().__init__("conference-model-service", base_url)
