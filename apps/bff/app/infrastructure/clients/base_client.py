from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class InternalResponse:
    status_code: int
    payload: Any
    www_authenticate: str | None = None


@dataclass(frozen=True)
class BaseInternalClient:
    service_name: str
    base_url: str

    @property
    def connection_status(self) -> str:
        return "not_connected"

    def request_headers(
        self,
        correlation_id: str,
        authorization: str | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, str]:
        headers = {"X-Correlation-Id": correlation_id}
        if authorization:
            headers["Authorization"] = authorization
        if client_ip:
            headers["X-Client-IP"] = client_ip
        if user_agent:
            headers["User-Agent"] = user_agent
        return headers

    async def request(
        self,
        method: str,
        path: str,
        correlation_id: str,
        authorization: str | None = None,
        json: dict[str, Any] | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> InternalResponse:
        request_options: dict[str, Any] = {}
        if json is not None:
            request_options["json"] = json
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.request(
                method,
                path,
                headers=self.request_headers(
                    correlation_id, authorization, client_ip, user_agent
                ),
                **request_options,
            )
        try:
            payload: Any = response.json()
        except ValueError:
            payload = {
                "error": {
                    "code": "INVALID_UPSTREAM_RESPONSE",
                    "message": "Identity Service returned a non-JSON response",
                }
            }
        return InternalResponse(
            status_code=response.status_code,
            payload=payload,
            www_authenticate=response.headers.get("WWW-Authenticate"),
        )
