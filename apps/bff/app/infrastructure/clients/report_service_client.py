from app.infrastructure.clients.base_client import BaseInternalClient


class ReportServiceClient(BaseInternalClient):
    def __init__(self, base_url: str) -> None:
        super().__init__("report-service", base_url)
