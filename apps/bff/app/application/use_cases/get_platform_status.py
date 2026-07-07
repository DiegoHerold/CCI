from app.infrastructure.clients.base_client import BaseInternalClient
from app.schemas.platform import PlatformStatusResponse


def get_platform_status(
    clients: dict[str, BaseInternalClient],
) -> PlatformStatusResponse:
    return PlatformStatusResponse(
        services={
            service_name: client.connection_status
            for service_name, client in clients.items()
        }
    )
