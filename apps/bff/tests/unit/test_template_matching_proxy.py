from typing import Any

from fastapi.testclient import TestClient

from app.dependencies import get_template_service_client
from app.infrastructure.clients.base_client import InternalResponse
from app.main import app


class FakeTemplateMatchingClient:
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


fake_matching_client = FakeTemplateMatchingClient()


def _with_fake_client() -> object | None:
    previous = app.dependency_overrides.get(get_template_service_client)
    app.dependency_overrides[get_template_service_client] = lambda: fake_matching_client
    return previous


def _restore_fake_client(previous: object | None) -> None:
    if previous is None:
        app.dependency_overrides.pop(get_template_service_client, None)
    else:
        app.dependency_overrides[get_template_service_client] = previous


def test_document_template_match_proxy_uses_template_service() -> None:
    previous = _with_fake_client()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/documents/doc-1/template-match",
                headers={"Authorization": "Bearer token"},
                json={"forceReprocess": True, "maxCandidates": 3},
            )
    finally:
        _restore_fake_client(previous)

    assert response.status_code == 200
    assert fake_matching_client.method == "POST"
    assert fake_matching_client.path == "/template-matching/documents/doc-1/match"
    assert fake_matching_client.authorization == "Bearer token"
    assert fake_matching_client.payload == {"forceReprocess": True, "maxCandidates": 3}


def test_document_template_match_confirm_proxy() -> None:
    previous = _with_fake_client()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/documents/doc-1/template-match/confirm",
                headers={"Authorization": "Bearer token"},
                json={"templateId": "tpl-1", "templateVersionId": "ver-1", "reason": "manual"},
            )
    finally:
        _restore_fake_client(previous)

    assert response.status_code == 200
    assert fake_matching_client.path == "/template-matching/documents/doc-1/confirm"
