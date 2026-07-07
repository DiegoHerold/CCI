from app.infrastructure.clients.base_client import BaseInternalClient


class ScheduleServiceClient(BaseInternalClient):
    def __init__(self, base_url: str) -> None:
        super().__init__("schedule-service", base_url)
