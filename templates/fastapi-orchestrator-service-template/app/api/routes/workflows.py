from fastapi import APIRouter, status

from app.config import get_settings


router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/placeholder", status_code=status.HTTP_202_ACCEPTED)
async def placeholder_workflow() -> dict[str, str]:
    settings = get_settings()
    return {
        "service": settings.service_name,
        "status": "accepted",
        "message": "workflow placeholder route - not implemented yet",
    }
