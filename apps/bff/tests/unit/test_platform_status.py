from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


EXPECTED_SERVICES = {
    "identity-service",
    "client-service",
    "document-service",
    "template-service",
    "extraction-service",
    "conference-model-service",
    "schedule-service",
    "document-ingestion-service",
    "document-classification-service",
    "variable-registry-service",
    "rule-service",
    "execution-control-service",
    "result-service",
    "audit-service",
    "report-service",
    "log-service",
}


def test_platform_status_is_placeholder() -> None:
    response = client.get("/api/v1/platform/status")
    payload = response.json()

    assert response.status_code == 200
    assert payload["platform"] == "cci-platform"
    assert payload["status"] == "bootstrapped"
    assert payload["phase"] == "fase-3-bff-inicial"
    assert set(payload["services"]) == EXPECTED_SERVICES
    assert set(payload["services"].values()) == {"not_connected"}


def test_remaining_placeholder_execution_list_is_empty() -> None:
    executions_response = client.get("/api/v1/executions")

    assert executions_response.status_code == 200
    assert executions_response.json()["items"] == []
    assert executions_response.json()["total"] == 0
    assert executions_response.json()["source"] == "placeholder"
