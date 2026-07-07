from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.dependencies import get_identity_client
from app.infrastructure.clients.base_client import InternalResponse
from app.infrastructure.clients.identity_client import IdentityClient


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def proxy_response(response: InternalResponse) -> JSONResponse:
    headers = {"Cache-Control": "no-store"}
    if response.www_authenticate:
        headers["WWW-Authenticate"] = response.www_authenticate
    return JSONResponse(
        status_code=response.status_code,
        content=response.payload,
        headers=headers,
    )


def identity_unavailable(exc: httpx.RequestError) -> HTTPException:
    return HTTPException(status_code=503, detail="identity-service unavailable")


def _request_metadata(request: Request) -> tuple[str | None, str | None]:
    client_ip = request.client.host if request.client else None
    return client_ip, request.headers.get("User-Agent")


def _set_refresh_cookie(
    response: JSONResponse, token: str, settings: Settings
) -> None:
    response.set_cookie(
        key=settings.auth_refresh_cookie_name,
        value=token,
        max_age=settings.auth_refresh_cookie_max_age,
        httponly=True,
        secure=settings.auth_refresh_cookie_secure,
        samesite=settings.auth_refresh_cookie_samesite,
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: JSONResponse, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.auth_refresh_cookie_name,
        httponly=True,
        secure=settings.auth_refresh_cookie_secure,
        samesite=settings.auth_refresh_cookie_samesite,
        path="/api/v1/auth",
    )


async def _identity_call(
    identity: IdentityClient,
    request: Request,
    method: str,
    path: str,
    authorization: str | None = None,
    payload: dict[str, Any] | None = None,
) -> InternalResponse:
    client_ip, user_agent = _request_metadata(request)
    try:
        return await identity.call(
            method,
            path,
            request.state.correlation_id,
            authorization=authorization,
            payload=payload,
            client_ip=client_ip,
            user_agent=user_agent,
        )
    except httpx.RequestError as exc:
        raise identity_unavailable(exc) from exc


@router.post("/login")
async def login(
    request: Request,
    payload: Annotated[dict[str, Any], Body()],
    identity: Annotated[IdentityClient, Depends(get_identity_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JSONResponse:
    upstream = await _identity_call(
        identity, request, "POST", "/auth/login", payload=payload
    )
    if upstream.status_code == 200 and isinstance(upstream.payload, dict):
        public_payload = dict(upstream.payload)
        refresh_token = public_payload.pop("refreshToken", None)
        response = proxy_response(
            InternalResponse(
                upstream.status_code,
                public_payload,
                upstream.www_authenticate,
            )
        )
        if isinstance(refresh_token, str):
            _set_refresh_cookie(response, refresh_token, settings)
        return response
    return proxy_response(upstream)


@router.post("/refresh")
async def refresh(
    request: Request,
    identity: Annotated[IdentityClient, Depends(get_identity_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JSONResponse:
    refresh_token = request.cookies.get(settings.auth_refresh_cookie_name)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="refresh token missing")
    return proxy_response(
        await _identity_call(
            identity,
            request,
            "POST",
            "/auth/refresh",
            payload={"refreshToken": refresh_token},
        )
    )


@router.post("/logout")
async def logout(
    request: Request,
    identity: Annotated[IdentityClient, Depends(get_identity_client)],
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    refresh_token = request.cookies.get(settings.auth_refresh_cookie_name)
    upstream = await _identity_call(
        identity,
        request,
        "POST",
        "/auth/logout",
        authorization=authorization,
        payload={"refreshToken": refresh_token} if refresh_token else None,
    )
    response = proxy_response(upstream)
    _clear_refresh_cookie(response, settings)
    return response


@router.post("/logout-all")
async def logout_all(
    request: Request,
    identity: Annotated[IdentityClient, Depends(get_identity_client)],
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    upstream = await _identity_call(
        identity,
        request,
        "POST",
        "/auth/logout-all",
        authorization=authorization,
    )
    response = proxy_response(upstream)
    _clear_refresh_cookie(response, settings)
    return response


@router.post("/change-password")
async def change_password(
    request: Request,
    payload: Annotated[dict[str, Any], Body()],
    identity: Annotated[IdentityClient, Depends(get_identity_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return proxy_response(
        await _identity_call(
            identity,
            request,
            "POST",
            "/auth/change-password",
            authorization=authorization,
            payload=payload,
        )
    )


@router.get("/me")
async def current_user(
    request: Request,
    identity: Annotated[IdentityClient, Depends(get_identity_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return proxy_response(
        await _identity_call(
            identity,
            request,
            "GET",
            "/auth/me",
            authorization=authorization,
        )
    )
