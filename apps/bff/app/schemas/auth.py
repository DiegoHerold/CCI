from typing import Literal

from pydantic import BaseModel, Field


class DevelopmentUser(BaseModel):
    user_id: str = "dev_user"
    name: str = "Development User"
    email: str = "dev@cci.local"
    roles: list[str] = Field(default_factory=lambda: ["admin"])
    permissions: list[str] = Field(default_factory=lambda: ["*"])
    client_ids: list[str] = Field(default_factory=list)


class AuthMeResponse(BaseModel):
    user: DevelopmentUser = Field(default_factory=DevelopmentUser)
    auth_mode: Literal["development_placeholder"] = "development_placeholder"
