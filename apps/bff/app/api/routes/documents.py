from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.routes.auth import proxy_response
from app.dependencies import get_document_service_client
from app.infrastructure.clients.document_service_client import DocumentServiceClient


router = APIRouter(prefix="/api/v1", tags=["documents"])


def _request_metadata(request: Request) -> tuple[str | None, str | None]:
    client_ip = request.client.host if request.client else None
    return client_ip, request.headers.get("User-Agent")


async def _proxy_json(
    request: Request,
    path: str,
    document_service: DocumentServiceClient,
    authorization: str | None,
) -> JSONResponse:
    payload: dict[str, Any] | None = None
    if request.method in {"POST", "PATCH", "PUT"}:
        body = await request.body()
        if body:
            payload = await request.json()
    client_ip, user_agent = _request_metadata(request)
    try:
        upstream = await document_service.call(
            request.method,
            path,
            request.state.correlation_id,
            authorization=authorization,
            payload=payload,
            params=list(request.query_params.multi_items()),
            client_ip=client_ip,
            user_agent=user_agent,
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="document-service unavailable") from exc
    return proxy_response(upstream)


async def _proxy_raw(
    request: Request,
    path: str,
    document_service: DocumentServiceClient,
    authorization: str | None,
) -> JSONResponse:
    client_ip, user_agent = _request_metadata(request)
    try:
        upstream = await document_service.call_raw(
            request.method,
            path,
            request.state.correlation_id,
            authorization=authorization,
            body=await request.body(),
            content_type=request.headers.get("Content-Type"),
            client_ip=client_ip,
            user_agent=user_agent,
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="document-service unavailable") from exc
    return proxy_response(upstream)


@router.post("/documents/upload")
async def upload_document(
    request: Request,
    document_service: Annotated[DocumentServiceClient, Depends(get_document_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy_raw(request, "/documents/upload", document_service, authorization)


@router.post("/documents/upload-zip")
async def upload_zip(
    request: Request,
    document_service: Annotated[DocumentServiceClient, Depends(get_document_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy_raw(request, "/documents/upload-zip", document_service, authorization)


@router.api_route("/documents", methods=["GET"])
async def documents_root(
    request: Request,
    document_service: Annotated[DocumentServiceClient, Depends(get_document_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy_json(request, "/documents", document_service, authorization)


@router.api_route("/documents/{path:path}", methods=["GET", "POST", "PATCH"])
async def documents_nested(
    path: str,
    request: Request,
    document_service: Annotated[DocumentServiceClient, Depends(get_document_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy_json(request, f"/documents/{path}", document_service, authorization)
