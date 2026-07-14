from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.routes.auth import proxy_response
from app.dependencies import get_template_service_client
from app.infrastructure.clients.template_service_client import TemplateServiceClient


router = APIRouter(prefix="/api/v1", tags=["template-matching"])


async def _proxy(
    request: Request,
    path: str,
    template_service: TemplateServiceClient,
    authorization: str | None,
) -> JSONResponse:
    payload: dict[str, Any] | None = None
    if request.method in {"POST", "PATCH", "PUT"}:
        body = await request.body()
        if body:
            payload = await request.json()
    client_ip = request.client.host if request.client else None
    try:
        upstream = await template_service.call(
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
        raise HTTPException(status_code=503, detail="template-service unavailable") from exc
    return proxy_response(upstream)


@router.post("/documents/{document_id}/template-match")
async def match_document_template(
    document_id: str,
    request: Request,
    template_service: Annotated[TemplateServiceClient, Depends(get_template_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(
        request,
        f"/template-matching/documents/{document_id}/match",
        template_service,
        authorization,
    )


@router.get("/documents/{document_id}/template-match")
async def get_document_template_match(
    document_id: str,
    request: Request,
    template_service: Annotated[TemplateServiceClient, Depends(get_template_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(
        request,
        f"/template-matching/documents/{document_id}",
        template_service,
        authorization,
    )


@router.get("/documents/{document_id}/template-match/runs")
async def list_document_template_match_runs(
    document_id: str,
    request: Request,
    template_service: Annotated[TemplateServiceClient, Depends(get_template_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(
        request,
        f"/template-matching/documents/{document_id}/runs",
        template_service,
        authorization,
    )


@router.post("/documents/{document_id}/template-match/confirm")
async def confirm_document_template_match(
    document_id: str,
    request: Request,
    template_service: Annotated[TemplateServiceClient, Depends(get_template_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(
        request,
        f"/template-matching/documents/{document_id}/confirm",
        template_service,
        authorization,
    )
