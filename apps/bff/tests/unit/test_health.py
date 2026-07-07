from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_200() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "bff",
        "status": "ok",
        "env": "development",
    }
    assert response.headers["X-Correlation-Id"]


def test_ready_validates_basic_configuration() -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "service": "bff",
        "status": "ready",
        "checks": {"config": "ok"},
    }
