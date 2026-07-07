from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.routes.auth import proxy_response
from app.dependencies import get_identity_client
from app.infrastructure.clients.identity_client import IdentityClient


router = APIRouter(prefix="/api/v1/users", tags=["users"])


async def call_identity(
    identity: IdentityClient,
    method: str,
    path: str,
    request: Request,
    authorization: str | None,
    payload: dict[str, Any] | None = None,
) -> JSONResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    try:
        response = await identity.users(
            method,
            path,
            authorization,
            request.state.correlation_id,
            payload,
            client_ip,
            user_agent,
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503, detail="identity-service unavailable"
        ) from exc
    return proxy_response(response)


@router.get("")
async def list_users(
    request: Request,
    identity: Annotated[IdentityClient, Depends(get_identity_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await call_identity(identity, "GET", "/users", request, authorization)


@router.post("")
async def create_user(
    request: Request,
    payload: Annotated[dict[str, Any], Body()],
    identity: Annotated[IdentityClient, Depends(get_identity_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await call_identity(
        identity, "POST", "/users", request, authorization, payload
    )


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    request: Request,
    identity: Annotated[IdentityClient, Depends(get_identity_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await call_identity(
        identity, "GET", f"/users/{user_id}", request, authorization
    )


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    request: Request,
    payload: Annotated[dict[str, Any], Body()],
    identity: Annotated[IdentityClient, Depends(get_identity_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await call_identity(
        identity,
        "PATCH",
        f"/users/{user_id}",
        request,
        authorization,
        payload,
    )


@router.patch("/{user_id}/disable")
async def disable_user(
    user_id: str,
    request: Request,
    identity: Annotated[IdentityClient, Depends(get_identity_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await call_identity(
        identity,
        "PATCH",
        f"/users/{user_id}/disable",
        request,
        authorization,
    )


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    request: Request,
    payload: Annotated[dict[str, Any], Body()],
    identity: Annotated[IdentityClient, Depends(get_identity_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await call_identity(
        identity,
        "POST",
        f"/users/{user_id}/reset-password",
        request,
        authorization,
        payload,
    )
