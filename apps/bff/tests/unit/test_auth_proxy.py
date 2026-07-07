from typing import Any

from fastapi.testclient import TestClient

from app.dependencies import get_identity_client
from app.infrastructure.clients.base_client import InternalResponse
from app.main import app


class FakeIdentityClient:
    last_authorization: str | None = None
    last_correlation_id: str | None = None
    last_path: str | None = None
    last_payload: dict[str, Any] | None = None

    async def call(
        self,
        method: str,
        path: str,
        correlation_id: str,
        authorization: str | None = None,
        payload: dict[str, Any] | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> InternalResponse:
        self.last_authorization = authorization
        self.last_correlation_id = correlation_id
        self.last_path = path
        self.last_payload = payload
        if path == "/auth/login":
            return InternalResponse(
                200,
                {
                    "accessToken": "signed-token",
                    "refreshToken": "refresh-secret",
                    "tokenType": "Bearer",
                    "expiresIn": 900,
                    "user": {"email": payload["email"] if payload else None},
                },
            )
        if path == "/auth/refresh":
            return InternalResponse(
                200,
                {"accessToken": "renewed-token", "tokenType": "Bearer", "expiresIn": 900},
            )
        if path == "/auth/me":
            return InternalResponse(
                200,
                {
                    "id": "user-id",
                    "email": "admin@example.com",
                    "status": "ACTIVE",
                    "roles": ["ADMIN"],
                    "permissions": ["users:read"],
                },
            )
        return InternalResponse(200, {"success": True})

    async def users(
        self,
        method: str,
        path: str,
        authorization: str | None,
        correlation_id: str,
        payload: dict[str, Any] | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> InternalResponse:
        self.last_authorization = authorization
        self.last_correlation_id = correlation_id
        self.last_path = path
        self.last_payload = payload
        return InternalResponse(200, [{"id": "user-id", "status": "ACTIVE"}])


fake_identity = FakeIdentityClient()
app.dependency_overrides[get_identity_client] = lambda: fake_identity
client = TestClient(app)


def test_login_sets_http_only_refresh_cookie_and_hides_token() -> None:
    response = client.post(
        "/api/v1/auth/login",
        headers={"X-Correlation-Id": "correlation-login"},
        json={"email": "admin@example.com", "password": "secret"},
    )

    assert response.status_code == 200
    assert response.json()["accessToken"] == "signed-token"
    assert "refreshToken" not in response.json()
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]
    assert fake_identity.last_correlation_id == "correlation-login"


def test_refresh_uses_http_only_cookie() -> None:
    client.cookies.set("cci_refresh_token", "refresh-secret", path="/api/v1/auth")

    response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 200
    assert response.json()["accessToken"] == "renewed-token"
    assert fake_identity.last_payload == {"refreshToken": "refresh-secret"}


def test_logout_propagates_token_and_clears_cookie() -> None:
    client.cookies.set("cci_refresh_token", "refresh-secret", path="/api/v1/auth")

    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": "Bearer signed-token"},
    )

    assert response.status_code == 200
    assert fake_identity.last_authorization == "Bearer signed-token"
    assert fake_identity.last_payload == {"refreshToken": "refresh-secret"}
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_me_propagates_bearer_token() -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer signed-token",
            "X-Correlation-Id": "correlation-me",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ACTIVE"
    assert fake_identity.last_authorization == "Bearer signed-token"
    assert fake_identity.last_correlation_id == "correlation-me"


def test_users_route_propagates_bearer_token() -> None:
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": "Bearer signed-token"},
    )

    assert response.status_code == 200
    assert response.json()[0]["id"] == "user-id"
    assert fake_identity.last_authorization == "Bearer signed-token"


def test_reset_password_route_is_proxied() -> None:
    response = client.post(
        "/api/v1/users/user-id/reset-password",
        headers={"Authorization": "Bearer signed-token"},
        json={"newPassword": "ResetPassword123!"},
    )

    assert response.status_code == 200
    assert fake_identity.last_path == "/users/user-id/reset-password"
