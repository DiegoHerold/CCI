from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_auth_me_returns_development_user() -> None:
    response = client.get("/api/v1/auth/me")
    payload = response.json()

    assert response.status_code == 200
    assert payload["auth_mode"] == "development_placeholder"
    assert payload["user"] == {
        "user_id": "dev_user",
        "name": "Development User",
        "email": "dev@cci.local",
        "roles": ["admin"],
        "permissions": ["*"],
        "client_ids": [],
    }
