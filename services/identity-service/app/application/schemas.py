from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.domain.access import RoleName, UserStatus
from app.infrastructure.database.models import User
from app.infrastructure.repositories import get_permission_names, get_role_names


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class LoginRequest(ApiModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class UserCreate(ApiModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)
    roles: list[RoleName] = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("name is required")
        return value

    @field_validator("roles")
    @classmethod
    def unique_roles(cls, value: list[RoleName]) -> list[RoleName]:
        if len(value) != len(set(value)):
            raise ValueError("roles must be unique")
        return value


class UserUpdate(ApiModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    roles: list[RoleName] | None = Field(default=None, min_length=1)
    status: UserStatus | None = None

    @field_validator("name")
    @classmethod
    def strip_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if len(value) < 2:
            raise ValueError("name is required")
        return value

    @field_validator("roles")
    @classmethod
    def unique_optional_roles(
        cls, value: list[RoleName] | None
    ) -> list[RoleName] | None:
        if value is not None and len(value) != len(set(value)):
            raise ValueError("roles must be unique")
        return value

    @model_validator(mode="after")
    def require_change(self) -> "UserUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        return self


class AuthenticatedUser(ApiModel):
    id: str
    name: str
    email: EmailStr
    status: UserStatus
    roles: list[str]
    permissions: list[str]

    @classmethod
    def from_entity(cls, user: User) -> "AuthenticatedUser":
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            status=UserStatus(user.status),
            roles=get_role_names(user),
            permissions=get_permission_names(user),
        )


class UserResponse(AuthenticatedUser):
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            status=UserStatus(user.status),
            roles=get_role_names(user),
            permissions=get_permission_names(user),
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class LoginResponse(ApiModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: AuthenticatedUser


class RefreshRequest(ApiModel):
    refresh_token: str = Field(min_length=1, max_length=4096)


class RefreshResponse(ApiModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class LogoutRequest(ApiModel):
    refresh_token: str | None = Field(default=None, max_length=4096)


class ChangePasswordRequest(ApiModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=1, max_length=256)


class ResetPasswordRequest(ApiModel):
    new_password: str = Field(min_length=1, max_length=256)


class SuccessResponse(ApiModel):
    success: bool = True
