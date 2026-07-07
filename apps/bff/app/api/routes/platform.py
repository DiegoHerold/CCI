from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.use_cases.get_platform_status import get_platform_status
from app.dependencies import get_internal_clients
from app.infrastructure.clients.base_client import BaseInternalClient
from app.schemas.platform import PlatformStatusResponse


router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


@router.get("/status", response_model=PlatformStatusResponse)
async def platform_status(
    clients: Annotated[dict[str, BaseInternalClient], Depends(get_internal_clients)],
) -> PlatformStatusResponse:
    return get_platform_status(clients)
