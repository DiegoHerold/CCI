from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_cors_allows_local_web_origin() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["X-Correlation-Id"]
