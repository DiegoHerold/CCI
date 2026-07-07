from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    ADMIN = "admin"
    COORDINATOR = "coordinator"
    ANALYST = "analyst"
    REVIEWER = "reviewer"
    READ_ONLY = "read_only"


ALL_PERMISSIONS = frozenset(
    {
        "users.create", "users.read", "users.update", "users.disable",
        "clients.create", "clients.read", "clients.update", "clients.delete", "clients.assign_user",
        "models.create", "models.read", "models.update", "models.version", "models.activate",
        "documents.import", "documents.read", "documents.confirm", "documents.reject",
        "variables.read", "variables.confirm", "variables.correct", "variables.ignore",
        "rules.create", "rules.read", "rules.update", "rules.version", "rules.activate", "rules.disable",
        "executions.start", "executions.read", "executions.cancel", "executions.reprocess",
        "results.read", "audit.read", "reports.generate", "reports.read", "reports.download", "logs.read",
    }
)

ROLE_PERMISSIONS: dict[Role, frozenset[str]] = {
    Role.ADMIN: ALL_PERMISSIONS,
    Role.COORDINATOR: ALL_PERMISSIONS
    - {"users.create", "users.disable", "clients.delete"},
    Role.ANALYST: frozenset(
        {
            "clients.read", "clients.update", "models.read",
            "documents.import", "documents.read", "documents.confirm", "documents.reject",
            "variables.read", "variables.confirm", "variables.correct", "variables.ignore",
            "rules.create", "rules.read", "rules.update", "rules.version",
            "executions.start", "executions.read", "executions.reprocess",
            "results.read", "audit.read", "reports.generate", "reports.read",
            "reports.download", "logs.read",
        }
    ),
    Role.REVIEWER: frozenset(
        {
            "clients.read", "models.read", "documents.read", "documents.confirm", "documents.reject",
            "variables.read", "variables.confirm", "variables.correct", "variables.ignore",
            "rules.read", "executions.read", "results.read", "audit.read",
            "reports.generate", "reports.read", "reports.download", "logs.read",
        }
    ),
    Role.READ_ONLY: frozenset(
        {
            "users.read", "clients.read", "models.read", "documents.read", "variables.read",
            "rules.read", "executions.read", "results.read", "audit.read", "reports.read",
            "reports.download", "logs.read",
        }
    ),
}


class UserClaims(BaseModel):
    sub: str
    email: str
    name: str
    roles: list[Role] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    client_ids: list[str] = Field(default_factory=list)
    iat: int
    exp: int


def has_role(user_claims: UserClaims, role: Role | str) -> bool:
    expected = Role(role)
    return expected in user_claims.roles


def has_permission(user_claims: UserClaims, permission: str) -> bool:
    if Role.ADMIN in user_claims.roles:
        return True
    if permission in user_claims.permissions:
        return True
    return any(
        permission in ROLE_PERMISSIONS.get(role, frozenset())
        for role in user_claims.roles
    )


def can_access_client(user_claims: UserClaims, client_id: str) -> bool:
    return Role.ADMIN in user_claims.roles or client_id in user_claims.client_ids
