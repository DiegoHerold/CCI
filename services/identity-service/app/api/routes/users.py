from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.application.context import context_from_request
from app.application.schemas import (
    ResetPasswordRequest,
    SuccessResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.application.services import IdentityService
from app.dependencies import require_permission
from app.domain.access import PermissionName
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db


router = APIRouter(prefix="/users", tags=["users"])


UsersRead = Annotated[
    User, Depends(require_permission(PermissionName.USERS_READ))
]
UsersCreate = Annotated[
    User, Depends(require_permission(PermissionName.USERS_CREATE))
]
UsersUpdate = Annotated[
    User, Depends(require_permission(PermissionName.USERS_UPDATE))
]
UsersDisable = Annotated[
    User, Depends(require_permission(PermissionName.USERS_DISABLE))
]
UsersResetPassword = Annotated[
    User, Depends(require_permission(PermissionName.USERS_RESET_PASSWORD))
]


@router.get("", response_model=list[UserResponse])
def list_users(
    _: UsersRead,
    session: Annotated[Session, Depends(get_db)],
) -> list[UserResponse]:
    return [
        UserResponse.from_entity(user)
        for user in IdentityService(session).list_users()
    ]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    _: UsersCreate,
    session: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    user = IdentityService(session).create_user(payload)
    return UserResponse.from_entity(user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    _: UsersRead,
    session: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    return UserResponse.from_entity(IdentityService(session).get_user(user_id))


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    request: Request,
    payload: UserUpdate,
    actor: UsersUpdate,
    session: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    return UserResponse.from_entity(
        IdentityService(session).update_user(
            user_id, payload, actor=actor, context=context_from_request(request)
        )
    )


@router.patch("/{user_id}/disable", response_model=UserResponse)
def disable_user(
    user_id: str,
    request: Request,
    actor: UsersDisable,
    session: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    return UserResponse.from_entity(
        IdentityService(session).disable_user(
            user_id, actor, context_from_request(request)
        )
    )


@router.post("/{user_id}/reset-password", response_model=SuccessResponse)
def reset_password(
    user_id: str,
    request: Request,
    payload: ResetPasswordRequest,
    actor: UsersResetPassword,
    session: Annotated[Session, Depends(get_db)],
) -> SuccessResponse:
    IdentityService(session).reset_password(
        user_id,
        payload.new_password,
        actor,
        context_from_request(request),
    )
    return SuccessResponse()
