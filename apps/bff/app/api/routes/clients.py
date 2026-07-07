from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.routes.auth import proxy_response
from app.dependencies import get_client_service_client
from app.infrastructure.clients.client_service_client import ClientServiceClient


router = APIRouter(prefix="/api/v1", tags=["clients"])


async def _proxy(
    request: Request,
    path: str,
    client_service: ClientServiceClient,
    authorization: str | None,
) -> JSONResponse:
    payload: dict[str, Any] | None = None
    if request.method in {"POST", "PATCH", "PUT"}:
        body = await request.body()
        if body:
            payload = await request.json()
    client_ip = request.client.host if request.client else None
    try:
        upstream = await client_service.call(
            request.method,
            path,
            request.state.correlation_id,
            authorization=authorization,
            payload=payload,
            params=list(request.query_params.multi_items()),
            client_ip=client_ip,
            user_agent=request.headers.get("User-Agent"),
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="client-service unavailable") from exc
    return proxy_response(upstream)


@router.api_route("/clients", methods=["GET", "POST"])
async def clients_root(
    request: Request,
    client_service: Annotated[ClientServiceClient, Depends(get_client_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, "/clients", client_service, authorization)


@router.api_route(
    "/clients/{path:path}", methods=["GET", "POST", "PATCH", "DELETE"]
)
async def clients_nested(
    path: str,
    request: Request,
    client_service: Annotated[ClientServiceClient, Depends(get_client_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/clients/{path}", client_service, authorization)


@router.api_route("/client-context", methods=["GET"])
async def context_root(
    request: Request,
    client_service: Annotated[ClientServiceClient, Depends(get_client_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, "/client-context", client_service, authorization)


@router.api_route("/client-context/{path:path}", methods=["GET", "PATCH"])
async def context_nested(
    path: str,
    request: Request,
    client_service: Annotated[ClientServiceClient, Depends(get_client_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(
        request, f"/client-context/{path}", client_service, authorization
    )
