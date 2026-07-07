from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_logs_stream_is_finite_sse_placeholder() -> None:
    correlation_id = "corr-sse-test"
    response = client.get(
        "/api/v1/logs/stream",
        headers={"X-Correlation-Id": correlation_id},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["X-Correlation-Id"] == correlation_id
    assert "event: connected" in response.text
    assert "event: heartbeat" in response.text
    assert "event: placeholder_log" in response.text
    assert correlation_id in response.text
