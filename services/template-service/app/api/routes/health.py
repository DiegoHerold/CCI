from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "template-service"}


@router.get("/ready")
def ready() -> dict[str, object]:
    return {"status": "ready", "service": "template-service", "checks": {}}
