from fastapi import APIRouter

from app.config import get_settings


router = APIRouter(tags=["platform"])


@router.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "service": settings.service_name,
        "status": "ok",
        "env": settings.app_env,
    }


@router.get("/ready")
async def ready() -> dict[str, object]:
    settings = get_settings()
    return {
        "service": settings.service_name,
        "status": "ready",
        "checks": {"config": "ok"},
    }
