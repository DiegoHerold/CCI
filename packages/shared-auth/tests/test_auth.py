import sys
from pathlib import Path


PYTHON_DIR = Path(__file__).resolve().parents[1] / "python"
sys.path.insert(0, str(PYTHON_DIR))

from auth import (  # noqa: E402
    ALL_PERMISSIONS,
    Role,
    UserClaims,
    can_access_client,
    has_permission,
)


def claims(role: Role, client_ids: list[str] | None = None) -> UserClaims:
    return UserClaims(
        sub="user_123",
        email="usuario@empresa.com",
        name="Usuário",
        roles=[role],
        permissions=[],
        client_ids=client_ids or [],
        iat=1,
        exp=2,
    )


def test_admin_has_all_permissions() -> None:
    admin = claims(Role.ADMIN)

    assert all(has_permission(admin, permission) for permission in ALL_PERMISSIONS)


def test_read_only_cannot_create_client() -> None:
    assert not has_permission(claims(Role.READ_ONLY), "clients.create")


def test_analyst_can_import_document() -> None:
    assert has_permission(claims(Role.ANALYST), "documents.import")


def test_can_access_client_uses_claim_scope() -> None:
    analyst = claims(Role.ANALYST, ["client_123"])

    assert can_access_client(analyst, "client_123")
    assert not can_access_client(analyst, "client_999")
