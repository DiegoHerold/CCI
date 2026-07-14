from typing import Any

from fastapi.testclient import TestClient

from app.dependencies import get_extraction_service_client
from app.infrastructure.clients.base_client import InternalResponse
from app.main import app


class FakeExtractionClient:
    method: str | None = None
    path: str | None = None
    authorization: str | None = None
    payload: dict[str, Any] | None = None

    async def call(
        self,
        method: str,
        path: str,
        correlation_id: str,
        authorization: str | None = None,
        payload: dict[str, Any] | None = None,
        params: list[tuple[str, str]] | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> InternalResponse:
        self.method = method
        self.path = path
        self.authorization = authorization
        self.payload = payload
        return InternalResponse(200, {"path": path, "proxied": True})


fake_extraction_client = FakeExtractionClient()


def test_document_extract_proxy_uses_extraction_service_before_document_catch_all() -> None:
    previous = app.dependency_overrides.get(get_extraction_service_client)
    app.dependency_overrides[get_extraction_service_client] = lambda: fake_extraction_client
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/documents/doc-1/extract",
                headers={"Authorization": "Bearer token"},
                json={"forceReprocess": True},
            )
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_extraction_service_client, None)
        else:
            app.dependency_overrides[get_extraction_service_client] = previous

    assert response.status_code == 200
    assert fake_extraction_client.method == "POST"
    assert fake_extraction_client.path == "/extractions/documents/doc-1"
    assert fake_extraction_client.authorization == "Bearer token"
    assert fake_extraction_client.payload == {"forceReprocess": True}
