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
    CLIENTS_READ = "clients:read"
    CLIENTS_CREATE = "clients:create"
    CLIENTS_UPDATE = "clients:update"
    CLIENTS_DISABLE = "clients:disable"
    CLIENTS_ARCHIVE = "clients:archive"
    CLIENT_USERS_READ = "client-users:read"
    CLIENT_USERS_MANAGE = "client-users:manage"
    CLIENT_COMPETENCIES_READ = "client-competencies:read"
    CLIENT_COMPETENCIES_CREATE = "client-competencies:create"
    CLIENT_COMPETENCIES_UPDATE = "client-competencies:update"
    CLIENT_COMPETENCIES_CLOSE = "client-competencies:close"
    CLIENT_COMPETENCIES_ARCHIVE = "client-competencies:archive"
    CLIENT_FOLDERS_READ = "client-folders:read"
    CLIENT_FOLDERS_UPDATE = "client-folders:update"
    CLIENT_FOLDERS_PREVIEW = "client-folders:preview"
    CLIENT_CONTEXT_READ = "client-context:read"


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
            PermissionName.CLIENTS_READ,
            PermissionName.CLIENTS_UPDATE,
            PermissionName.CLIENT_USERS_READ,
            PermissionName.CLIENT_COMPETENCIES_READ,
            PermissionName.CLIENT_COMPETENCIES_CREATE,
            PermissionName.CLIENT_COMPETENCIES_UPDATE,
            PermissionName.CLIENT_COMPETENCIES_CLOSE,
            PermissionName.CLIENT_FOLDERS_READ,
            PermissionName.CLIENT_FOLDERS_UPDATE,
            PermissionName.CLIENT_FOLDERS_PREVIEW,
            PermissionName.CLIENT_CONTEXT_READ,
        }
    ),
    RoleName.OPERATOR: frozenset(
        {
            PermissionName.CONFERENCES_READ,
            PermissionName.CONFERENCES_CREATE,
            PermissionName.CONFERENCES_EXECUTE,
            PermissionName.CLIENTS_READ,
            PermissionName.CLIENT_COMPETENCIES_READ,
            PermissionName.CLIENT_COMPETENCIES_CREATE,
            PermissionName.CLIENT_COMPETENCIES_UPDATE,
            PermissionName.CLIENT_FOLDERS_READ,
            PermissionName.CLIENT_FOLDERS_PREVIEW,
            PermissionName.CLIENT_CONTEXT_READ,
        }
    ),
    RoleName.VIEWER: frozenset(
        {
            PermissionName.CONFERENCES_READ,
            PermissionName.CLIENTS_READ,
            PermissionName.CLIENT_COMPETENCIES_READ,
            PermissionName.CLIENT_FOLDERS_READ,
            PermissionName.CLIENT_FOLDERS_PREVIEW,
            PermissionName.CLIENT_CONTEXT_READ,
        }
    ),
}
