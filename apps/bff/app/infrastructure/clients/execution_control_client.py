from app.infrastructure.clients.base_client import BaseInternalClient


class ExecutionControlClient(BaseInternalClient):
    def __init__(self, base_url: str) -> None:
        super().__init__("execution-control-service", base_url)
