from app.infrastructure.clients.base_client import BaseInternalClient


class VariableRegistryClient(BaseInternalClient):
    def __init__(self, base_url: str) -> None:
        super().__init__("variable-registry-service", base_url)
