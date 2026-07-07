from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.application.schemas import UserCreate
from app.application.services import IdentityService
from app.domain.access import RoleName, UserStatus
from app.infrastructure.repositories import UserRepository


ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "AdminPassword123!"


def login(client: TestClient, email: str, password: str) -> dict:
    response = client.post(
        "/auth/login", json={"email": email, "password": password}
    )
    return {"response": response, "payload": response.json()}


def admin_token(client: TestClient) -> str:
    result = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    assert result["response"].status_code == 200
    return result["payload"]["accessToken"]


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_direct_user(
    session: Session, email: str, role: RoleName, status: UserStatus = UserStatus.ACTIVE
):
    user = IdentityService(session).create_user(
        UserCreate(
            name="Test User",
            email=email,
            password="UserPassword123!",
            roles=[role],
        )
    )
    if status is UserStatus.INACTIVE:
        user.status = status.value
        session.commit()
    return user


def test_login_with_valid_credentials(client: TestClient) -> None:
    result = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)

    assert result["response"].status_code == 200
    assert result["payload"]["tokenType"] == "Bearer"
    assert result["payload"]["expiresIn"] == 900
    assert result["payload"]["refreshToken"]
    assert result["payload"]["user"]["roles"] == ["ADMIN"]
    assert "passwordHash" not in result["payload"]["user"]


def test_login_with_invalid_password_is_generic(client: TestClient) -> None:
    result = login(client, ADMIN_EMAIL, "wrong-password")

    assert result["response"].status_code == 401
    assert result["payload"]["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_with_unknown_user_is_generic(client: TestClient) -> None:
    result = login(client, "missing@example.com", "wrong-password")

    assert result["response"].status_code == 401
    assert result["payload"]["error"]["code"] == "INVALID_CREDENTIALS"


def test_inactive_user_cannot_login(
    client: TestClient, db_session: Session
) -> None:
    create_direct_user(
        db_session, "inactive@example.com", RoleName.VIEWER, UserStatus.INACTIVE
    )

    result = login(client, "inactive@example.com", "UserPassword123!")

    assert result["response"].status_code == 401
    assert result["payload"]["error"]["code"] == "INVALID_CREDENTIALS"


def test_auth_me_with_valid_token(client: TestClient) -> None:
    response = client.get("/auth/me", headers=bearer(admin_token(client)))

    assert response.status_code == 200
    assert response.json()["email"] == ADMIN_EMAIL
    assert response.json()["status"] == "ACTIVE"


def test_auth_me_without_token(client: TestClient) -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_protected_route_without_permission(
    client: TestClient, db_session: Session
) -> None:
    create_direct_user(db_session, "viewer@example.com", RoleName.VIEWER)
    token = login(client, "viewer@example.com", "UserPassword123!")["payload"][
        "accessToken"
    ]

    response = client.get("/users", headers=bearer(token))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_can_create_user(client: TestClient) -> None:
    response = client.post(
        "/users",
        headers=bearer(admin_token(client)),
        json={
            "name": "New Operator",
            "email": "operator@example.com",
            "password": "OperatorPassword123!",
            "roles": ["OPERATOR"],
        },
    )

    assert response.status_code == 201
    assert response.json()["roles"] == ["OPERATOR"]
    assert "conferences:execute" in response.json()["permissions"]
    assert "clients:read" in response.json()["permissions"]
    assert "client-context:read" in response.json()["permissions"]
    assert "passwordHash" not in response.json()


def test_user_without_permission_cannot_create_user(
    client: TestClient, db_session: Session
) -> None:
    create_direct_user(db_session, "manager@example.com", RoleName.MANAGER)
    token = login(client, "manager@example.com", "UserPassword123!")["payload"][
        "accessToken"
    ]

    response = client.post(
        "/users",
        headers=bearer(token),
        json={
            "name": "Forbidden User",
            "email": "forbidden@example.com",
            "password": "ForbiddenPassword123!",
            "roles": ["VIEWER"],
        },
    )

    assert response.status_code == 403


def test_password_is_persisted_as_argon2_hash(
    client: TestClient, db_session: Session
) -> None:
    password = "NeverStorePlaintext123!"
    response = client.post(
        "/users",
        headers=bearer(admin_token(client)),
        json={
            "name": "Hashed User",
            "email": "hashed@example.com",
            "password": password,
            "roles": ["VIEWER"],
        },
    )

    assert response.status_code == 201
    stored = UserRepository(db_session).get_by_email("hashed@example.com")
    assert stored is not None
    assert stored.password_hash != password
    assert stored.password_hash.startswith("$argon2")


def test_seed_is_idempotent_and_preserves_admin_password(
    db_session: Session,
) -> None:
    repository = UserRepository(db_session)
    before = repository.get_by_email(ADMIN_EMAIL)
    assert before is not None
    password_hash = before.password_hash

    from app.config import get_settings
    from app.infrastructure.seed import seed_identity

    seed_identity(db_session, get_settings())
    after = repository.get_by_email(ADMIN_EMAIL)

    assert after is not None
    assert after.password_hash == password_hash
    assert len(repository.list_all()) == 1


def test_client_service_permissions_are_seeded_idempotently(
    db_session: Session,
) -> None:
    from app.config import get_settings
    from app.infrastructure.database.models import Permission, Role
    from app.infrastructure.seed import seed_identity

    seed_identity(db_session, get_settings())
    seed_identity(db_session, get_settings())

    assert db_session.get(Permission, "clients:read") is not None
    assert db_session.get(Permission, "client-context:read") is not None
    admin = db_session.get(Role, "ADMIN")
    viewer = db_session.get(Role, "VIEWER")
    assert admin is not None and "clients:create" in {
        permission.name for permission in admin.permissions
    }
    assert viewer is not None and "clients:read" in {
        permission.name for permission in viewer.permissions
    }


def test_admin_user_management_lifecycle(client: TestClient) -> None:
    headers = bearer(admin_token(client))
    created = client.post(
        "/users",
        headers=headers,
        json={
            "name": "Lifecycle User",
            "email": "lifecycle@example.com",
            "password": "LifecyclePassword123!",
            "roles": ["VIEWER"],
        },
    )
    user_id = created.json()["id"]

    listed = client.get("/users", headers=headers)
    fetched = client.get(f"/users/{user_id}", headers=headers)
    updated = client.patch(
        f"/users/{user_id}",
        headers=headers,
        json={"name": "Updated Lifecycle User", "roles": ["OPERATOR"]},
    )
    disabled = client.patch(f"/users/{user_id}/disable", headers=headers)
    relogin = login(client, "lifecycle@example.com", "LifecyclePassword123!")

    assert created.status_code == 201
    assert any(user["id"] == user_id for user in listed.json())
    assert fetched.status_code == 200
    assert updated.json()["roles"] == ["OPERATOR"]
    assert disabled.json()["status"] == "INACTIVE"
    assert relogin["response"].status_code == 401
