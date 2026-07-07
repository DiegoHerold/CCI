from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_placeholder_workflow_returns_202() -> None:
    response = client.post("/workflows/placeholder")

    assert response.status_code == 202
    assert response.json()["status"] == "accepted"
    assert response.json()["service"]


def test_placeholder_workflow_returns_correlation_id() -> None:
    correlation_id = "workflow-test-correlation-id"
    response = client.post(
        "/workflows/placeholder",
        headers={"X-Correlation-Id": correlation_id},
    )

    assert response.headers["X-Correlation-Id"] == correlation_id
