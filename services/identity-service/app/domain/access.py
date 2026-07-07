from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class RoleName(StrEnum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class PermissionName(StrEnum):
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DISABLE = "users:disable"
    USERS_RESET_PASSWORD = "users:reset-password"
    IDENTITY_READ = "identity:read"
    IDENTITY_MANAGE = "identity:manage"
    CONFERENCES_READ = "conferences:read"
    CONFERENCES_CREATE = "conferences:create"
    CONFERENCES_UPDATE = "conferences:update"
    CONFERENCES_EXECUTE = "conferences:execute"


ALL_PERMISSIONS = frozenset(PermissionName)

ROLE_PERMISSIONS: dict[RoleName, frozenset[PermissionName]] = {
    RoleName.ADMIN: ALL_PERMISSIONS,
    RoleName.MANAGER: frozenset(
        {
            PermissionName.USERS_READ,
            PermissionName.CONFERENCES_READ,
            PermissionName.CONFERENCES_CREATE,
            PermissionName.CONFERENCES_UPDATE,
            PermissionName.CONFERENCES_EXECUTE,
        }
    ),
    RoleName.OPERATOR: frozenset(
        {
            PermissionName.CONFERENCES_READ,
            PermissionName.CONFERENCES_CREATE,
            PermissionName.CONFERENCES_EXECUTE,
        }
    ),
    RoleName.VIEWER: frozenset({PermissionName.CONFERENCES_READ}),
}
