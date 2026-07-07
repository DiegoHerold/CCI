from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_200_and_service_name() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"]
    assert response.json()["status"] == "ok"
    assert response.json()["env"] == "development"
    assert response.headers["X-Correlation-Id"]


def test_ready_returns_200() -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["checks"] == {}


def test_health_returns_correlation_id_header() -> None:
    correlation_id = "test-correlation-id"
    response = client.get(
        "/health",
        headers={"X-Correlation-Id": correlation_id},
    )

    assert response.headers["X-Correlation-Id"] == correlation_id


def test_not_found_uses_standard_error_contract() -> None:
    response = client.get("/route-that-does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "HTTP_ERROR"
    assert response.json()["error"]["correlation_id"]
    assert response.headers["X-Correlation-Id"]
