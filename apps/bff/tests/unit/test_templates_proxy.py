from typing import Any

from fastapi.testclient import TestClient

from app.dependencies import get_template_service_client
from app.infrastructure.clients.base_client import InternalResponse
from app.main import app


class FakeTemplateServiceClient:
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


fake_template_service = FakeTemplateServiceClient()
app.dependency_overrides[get_template_service_client] = lambda: fake_template_service


def test_templates_proxy_propagates_auth_query_and_body() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/templates/template-1/fields?source=viewer",
            headers={"Authorization": "Bearer token"},
            json={"fieldPath": "empresa.cnpj", "fieldType": "cnpj"},
        )

    assert response.status_code == 200
    assert fake_template_service.path == "/templates/template-1/fields"
    assert fake_template_service.authorization == "Bearer token"
    assert fake_template_service.params == [("source", "viewer")]
    assert fake_template_service.payload == {"fieldPath": "empresa.cnpj", "fieldType": "cnpj"}


def test_template_categories_proxy() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/template-categories",
            headers={"Authorization": "Bearer token"},
        )

    assert response.status_code == 200
    assert fake_template_service.path == "/template-categories"
