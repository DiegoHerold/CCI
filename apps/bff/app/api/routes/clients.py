from fastapi import APIRouter

from app.schemas.common import PlaceholderListResponse


router = APIRouter(prefix="/api/v1/clients", tags=["clients"])


@router.get("", response_model=PlaceholderListResponse)
async def list_clients() -> PlaceholderListResponse:
    return PlaceholderListResponse(
        message="client-service not implemented yet",
    )
