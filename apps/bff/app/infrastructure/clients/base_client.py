from dataclasses import dataclass


@dataclass(frozen=True)
class BaseInternalClient:
    service_name: str
    base_url: str

    @property
    def connection_status(self) -> str:
        return "not_connected"

    def request_headers(self, correlation_id: str) -> dict[str, str]:
        """Headers que serão usados quando a comunicação interna for ativada."""
        return {"X-Correlation-Id": correlation_id}
