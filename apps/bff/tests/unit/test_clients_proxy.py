from typing import Any

from fastapi.testclient import TestClient

from app.dependencies import get_client_service_client
from app.infrastructure.clients.base_client import InternalResponse
from app.main import app


class FakeClientServiceClient:
    method: str | None = None
    path: str | None = None
    authorization: str | None = None
    payload: dict[str, Any] | None = None
    params: list[tuple[str, str]] | None = None

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
        self.params = params
        return InternalResponse(200, {"path": path, "proxied": True})


fake_client_service = FakeClientServiceClient()
app.dependency_overrides[get_client_service_client] = lambda: fake_client_service


def test_clients_proxy_propagates_auth_query_and_body() -> None:
    with TestClient(app) as client:
        response = client.patch(
            "/api/v1/clients/client-1/folder?source=web",
            headers={"Authorization": "Bearer token"},
            json={"defaultFolderPath": "R:\\Clientes"},
        )

    assert response.status_code == 200
    assert fake_client_service.path == "/clients/client-1/folder"
    assert fake_client_service.authorization == "Bearer token"
    assert fake_client_service.params == [("source", "web")]
    assert fake_client_service.payload == {"defaultFolderPath": "R:\\Clientes"}


def test_client_context_is_proxied() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/client-context",
            headers={"Authorization": "Bearer token"},
        )

    assert response.status_code == 200
    assert fake_client_service.path == "/client-context"
