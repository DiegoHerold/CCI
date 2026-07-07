from app.infrastructure.clients.base_client import BaseInternalClient


class RuleServiceClient(BaseInternalClient):
    def __init__(self, base_url: str) -> None:
        super().__init__("rule-service", base_url)
