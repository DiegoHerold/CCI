import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@pytest.mark.parametrize(
    "path",
    [
        "/health",
        "/ready",
        "/api/v1/platform/status",
        "/api/v1/auth/me",
        "/api/v1/clients",
        "/api/v1/executions",
    ],
)
def test_every_json_response_has_correlation_id(path: str) -> None:
    response = client.get(path)

    assert response.status_code == 200
    assert response.headers["X-Correlation-Id"]


def test_received_correlation_id_is_preserved() -> None:
    correlation_id = "corr-from-frontend"
    response = client.get(
        "/api/v1/platform/status",
        headers={"X-Correlation-Id": correlation_id},
    )

    assert response.headers["X-Correlation-Id"] == correlation_id


def test_http_error_uses_standard_contract() -> None:
    response = client.get("/route-that-does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "HTTP_ERROR"
    assert response.json()["error"]["correlation_id"]
    assert response.headers["X-Correlation-Id"]
