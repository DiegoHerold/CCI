from sqlalchemy import func, select
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.application.schemas import UserCreate
from app.application.services import IdentityService
from app.config import get_settings
from app.domain.access import RoleName, UserStatus
from app.domain.audit import IdentityAuditEventType
from app.infrastructure.database.models import AuthSession, IdentityAuditEvent
from app.infrastructure.repositories import UserRepository
from app.main import app


ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "AdminPassword123!"


def login(
    client: TestClient,
    email: str = ADMIN_EMAIL,
    password: str = ADMIN_PASSWORD,
):
    return client.post("/auth/login", json={"email": email, "password": password})


def bearer(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def create_user(
    session: Session,
    email: str,
    role: RoleName = RoleName.VIEWER,
    password: str = "UserPassword123!",
):
    return IdentityService(session).create_user(
        UserCreate(
            name="Security User",
            email=email,
            password=password,
            roles=[role],
        )
    )


def test_login_creates_hashed_persistent_session(
    client: TestClient, db_session: Session
) -> None:
    response = login(client)
    refresh_token = response.json()["refreshToken"]
    auth_session = db_session.scalar(select(AuthSession))

    assert response.status_code == 200
    assert response.json()["accessToken"]
    assert auth_session is not None
    assert auth_session.refresh_token_hash != refresh_token
    assert len(auth_session.refresh_token_hash) == 64


def test_valid_refresh_issues_new_access_token(client: TestClient) -> None:
    tokens = login(client).json()
    response = client.post(
        "/auth/refresh", json={"refreshToken": tokens["refreshToken"]}
    )

    assert response.status_code == 200
    assert response.json()["accessToken"] != tokens["accessToken"]
    assert "refreshToken" not in response.json()


def test_invalid_refresh_token_fails(client: TestClient) -> None:
    response = client.post("/auth/refresh", json={"refreshToken": "invalid"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"


def test_logout_revokes_session_and_refresh(client: TestClient) -> None:
    tokens = login(client).json()
    logout = client.post(
        "/auth/logout",
        headers=bearer(tokens["accessToken"]),
        json={"refreshToken": tokens["refreshToken"]},
    )
    refreshed = client.post(
        "/auth/refresh", json={"refreshToken": tokens["refreshToken"]}
    )

    assert logout.status_code == 200
    assert logout.json() == {"success": True}
    assert refreshed.status_code == 401


def test_logout_all_revokes_every_session(client: TestClient) -> None:
    first = login(client).json()
    second = login(client).json()

    response = client.post(
        "/auth/logout-all", headers=bearer(second["accessToken"])
    )

    assert response.status_code == 200
    for token in (first["refreshToken"], second["refreshToken"]):
        assert client.post(
            "/auth/refresh", json={"refreshToken": token}
        ).status_code == 401


def test_change_password_requires_correct_current_password(
    client: TestClient,
) -> None:
    tokens = login(client).json()
    response = client.post(
        "/auth/change-password",
        headers=bearer(tokens["accessToken"]),
        json={
            "currentPassword": "WrongPassword123!",
            "newPassword": "NewAdminPassword123!",
        },
    )

    assert response.status_code == 401


def test_change_password_revokes_other_sessions(client: TestClient) -> None:
    old_session = login(client).json()
    current_session = login(client).json()

    changed = client.post(
        "/auth/change-password",
        headers=bearer(current_session["accessToken"]),
        json={
            "currentPassword": ADMIN_PASSWORD,
            "newPassword": "NewAdminPassword123!",
        },
    )

    assert changed.status_code == 200
    assert client.post(
        "/auth/refresh", json={"refreshToken": old_session["refreshToken"]}
    ).status_code == 401
    assert client.post(
        "/auth/refresh", json={"refreshToken": current_session["refreshToken"]}
    ).status_code == 200


def test_admin_reset_password_revokes_target_sessions(
    client: TestClient, db_session: Session
) -> None:
    target = create_user(db_session, "target@example.com")
    target_tokens = login(
        client, "target@example.com", "UserPassword123!"
    ).json()
    admin_tokens = login(client).json()

    response = client.post(
        f"/users/{target.id}/reset-password",
        headers=bearer(admin_tokens["accessToken"]),
        json={"newPassword": "ResetPassword123!"},
    )

    assert response.status_code == 200
    assert client.post(
        "/auth/refresh", json={"refreshToken": target_tokens["refreshToken"]}
    ).status_code == 401
    assert login(client, "target@example.com", "ResetPassword123!").status_code == 200


def test_reset_password_requires_permission(
    client: TestClient, db_session: Session
) -> None:
    target = create_user(db_session, "target@example.com")
    viewer = create_user(db_session, "viewer-reset@example.com")
    viewer_tokens = login(
        client, viewer.email, "UserPassword123!"
    ).json()

    response = client.post(
        f"/users/{target.id}/reset-password",
        headers=bearer(viewer_tokens["accessToken"]),
        json={"newPassword": "ResetPassword123!"},
    )

    assert response.status_code == 403


def test_weak_password_is_rejected(client: TestClient) -> None:
    admin_tokens = login(client).json()
    response = client.post(
        "/users",
        headers=bearer(admin_tokens["accessToken"]),
        json={
            "name": "Weak User",
            "email": "weak@example.com",
            "password": "onlyletters",
            "roles": ["VIEWER"],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_failed_attempts_lock_account_and_generic_error(
    client: TestClient, db_session: Session
) -> None:
    for _ in range(5):
        response = login(client, ADMIN_EMAIL, "WrongPassword123!")
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"

    blocked = login(client)
    user = UserRepository(db_session).get_by_email(ADMIN_EMAIL)

    assert blocked.status_code == 401
    assert blocked.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert user is not None and user.locked_until is not None


def test_successful_login_resets_failure_counter(
    client: TestClient, db_session: Session
) -> None:
    login(client, ADMIN_EMAIL, "WrongPassword123!")
    login(client, ADMIN_EMAIL, "WrongPassword123!")

    assert login(client).status_code == 200
    user = UserRepository(db_session).get_by_email(ADMIN_EMAIL)
    assert user is not None
    assert user.failed_login_attempts == 0
    assert user.locked_until is None


def test_inactive_user_cannot_refresh(
    client: TestClient, db_session: Session
) -> None:
    user = create_user(db_session, "inactive-refresh@example.com")
    tokens = login(client, user.email, "UserPassword123!").json()
    user.status = UserStatus.INACTIVE.value
    db_session.commit()

    response = client.post(
        "/auth/refresh", json={"refreshToken": tokens["refreshToken"]}
    )

    assert response.status_code == 401


def test_audit_events_are_append_only_records(
    client: TestClient, db_session: Session
) -> None:
    bad_login = login(client, ADMIN_EMAIL, "WrongPassword123!")
    good_login = login(client)
    client.post(
        "/auth/refresh",
        json={"refreshToken": good_login.json()["refreshToken"]},
    )

    event_types = set(
        db_session.scalars(select(IdentityAuditEvent.event_type)).all()
    )
    assert bad_login.status_code == 401
    assert IdentityAuditEventType.AUTH_LOGIN_FAILED.value in event_types
    assert IdentityAuditEventType.AUTH_LOGIN_SUCCESS.value in event_types
    assert IdentityAuditEventType.AUTH_TOKEN_REFRESH.value in event_types


def test_login_rate_limit_is_enforced(client: TestClient) -> None:
    restrictive = get_settings().model_copy(
        update={"auth_login_rate_limit_max": 2}
    )
    app.dependency_overrides[get_settings] = lambda: restrictive

    login(client, "missing-one@example.com", "WrongPassword123!")
    login(client, "missing-two@example.com", "WrongPassword123!")
    limited = login(client, "missing-three@example.com", "WrongPassword123!")

    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_unknown_and_existing_users_share_generic_login_error(
    client: TestClient,
) -> None:
    existing = login(client, ADMIN_EMAIL, "WrongPassword123!")
    missing = login(client, "missing@example.com", "WrongPassword123!")

    assert existing.status_code == missing.status_code == 401
    assert existing.json()["error"]["code"] == missing.json()["error"]["code"]
