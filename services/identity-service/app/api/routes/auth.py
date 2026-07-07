from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.application.auth_service import AuthenticationService
from app.application.context import context_from_request
from app.application.schemas import (
    AuthenticatedUser,
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshRequest,
    RefreshResponse,
    SuccessResponse,
)
from app.config import Settings, get_settings
from app.dependencies import CurrentUser, Principal
from app.infrastructure.database.session import get_db


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    request: Request,
    payload: LoginRequest,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    result = AuthenticationService(session, settings).login(
        str(payload.email), payload.password, context_from_request(request)
    )
    return LoginResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        expires_in=settings.jwt_access_expires_in,
        user=AuthenticatedUser.from_entity(result.user),
    )


@router.post("/refresh", response_model=RefreshResponse)
def refresh(
    request: Request,
    payload: RefreshRequest,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RefreshResponse:
    access_token = AuthenticationService(session, settings).refresh(
        payload.refresh_token, context_from_request(request)
    )
    return RefreshResponse(
        access_token=access_token,
        expires_in=settings.jwt_access_expires_in,
    )


@router.post("/logout", response_model=SuccessResponse)
def logout(
    request: Request,
    principal: Principal,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    payload: LogoutRequest | None = None,
) -> SuccessResponse:
    AuthenticationService(session, settings).logout(
        principal.user,
        principal.session_id,
        context_from_request(request),
        payload.refresh_token if payload else None,
    )
    return SuccessResponse()


@router.post("/logout-all", response_model=SuccessResponse)
def logout_all(
    request: Request,
    principal: Principal,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuccessResponse:
    AuthenticationService(session, settings).logout_all(
        principal.user, context_from_request(request)
    )
    return SuccessResponse()


@router.post("/change-password", response_model=SuccessResponse)
def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    principal: Principal,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuccessResponse:
    AuthenticationService(session, settings).change_password(
        principal.user,
        principal.session_id,
        payload.current_password,
        payload.new_password,
        context_from_request(request),
    )
    return SuccessResponse()


@router.get("/me", response_model=AuthenticatedUser)
def current_user(user: CurrentUser) -> AuthenticatedUser:
    return AuthenticatedUser.from_entity(user)
