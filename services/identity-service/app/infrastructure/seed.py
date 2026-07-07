import logging

from sqlalchemy.orm import Session

from app.application.security import hash_password, validate_password_policy
from app.config import Settings, get_settings
from app.domain.access import (
    PermissionName,
    ROLE_PERMISSIONS,
    RoleName,
    UserStatus,
)
from app.infrastructure.database.models import Permission, Role, User
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.repositories import UserRepository


logger = logging.getLogger(__name__)

ROLE_DESCRIPTIONS = {
    RoleName.ADMIN: "Full administrative access",
    RoleName.MANAGER: "Manages operations and reads users",
    RoleName.OPERATOR: "Executes operational conference routines",
    RoleName.VIEWER: "Read-only conference access",
}


def seed_identity(session: Session, settings: Settings) -> None:
    permissions: dict[str, Permission] = {}
    for permission_name in PermissionName:
        permission = session.get(Permission, permission_name.value)
        if permission is None:
            permission = Permission(
                name=permission_name.value,
                description=f"Allows {permission_name.value}",
            )
            session.add(permission)
        permissions[permission_name.value] = permission

    roles: dict[str, Role] = {}
    for role_name in RoleName:
        role = session.get(Role, role_name.value)
        if role is None:
            role = Role(
                name=role_name.value,
                description=ROLE_DESCRIPTIONS[role_name],
            )
            session.add(role)
        role.permissions = [
            permissions[permission.value]
            for permission in sorted(
                ROLE_PERMISSIONS[role_name], key=lambda item: item.value
            )
        ]
        roles[role_name.value] = role

    session.flush()
    admin_values = (
        settings.seed_admin_name,
        settings.seed_admin_email,
        settings.seed_admin_password,
    )
    if any(admin_values) and not all(admin_values):
        raise RuntimeError(
            "SEED_ADMIN_NAME, SEED_ADMIN_EMAIL and SEED_ADMIN_PASSWORD "
            "must be configured together"
        )
    if all(admin_values):
        assert settings.seed_admin_name is not None
        assert settings.seed_admin_email is not None
        assert settings.seed_admin_password is not None
        repository = UserRepository(session)
        admin = repository.get_by_email(settings.seed_admin_email)
        if admin is None:
            validate_password_policy(
                settings.seed_admin_password.get_secret_value(),
                settings.seed_admin_name,
                settings.seed_admin_email,
            )
            admin = User(
                name=settings.seed_admin_name.strip(),
                email=settings.seed_admin_email.strip().lower(),
                password_hash=hash_password(
                    settings.seed_admin_password.get_secret_value()
                ),
                status=UserStatus.ACTIVE.value,
                roles=[roles[RoleName.ADMIN.value]],
            )
            session.add(admin)
            logger.info("initial administrator created")
        elif roles[RoleName.ADMIN.value] not in admin.roles:
            admin.roles.append(roles[RoleName.ADMIN.value])
            logger.info("administrator role ensured")
    else:
        logger.warning("administrator seed skipped: seed variables are not set")
    session.commit()


def main() -> None:
    with SessionLocal() as session:
        seed_identity(session, get_settings())


if __name__ == "__main__":
    main()
