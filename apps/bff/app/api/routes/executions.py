from fastapi import APIRouter

from app.schemas.common import PlaceholderListResponse


router = APIRouter(prefix="/api/v1/executions", tags=["executions"])


@router.get("", response_model=PlaceholderListResponse)
async def list_executions() -> PlaceholderListResponse:
    return PlaceholderListResponse(
        message="execution-control-service not implemented yet",
    )
