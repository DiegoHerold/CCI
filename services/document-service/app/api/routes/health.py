from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.infrastructure.database.session import get_db


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready(session: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    session.execute(text("SELECT 1"))
    return {"status": "ready", "checks": {"database": "ok"}}
