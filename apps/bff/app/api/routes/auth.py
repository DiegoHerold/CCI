from fastapi import APIRouter

from app.schemas.auth import AuthMeResponse


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/me", response_model=AuthMeResponse)
async def current_user() -> AuthMeResponse:
    # Placeholder exclusivo de desenvolvimento. O identity-service substituirá
    # este contrato quando autenticação real entrar em uma fase futura.
    return AuthMeResponse()
