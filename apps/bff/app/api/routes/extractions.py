from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.routes.auth import proxy_response
from app.dependencies import get_extraction_service_client
from app.infrastructure.clients.extraction_service_client import ExtractionServiceClient


router = APIRouter(prefix="/api/v1", tags=["extractions"])


async def _proxy(
    request: Request,
    path: str,
    extraction_service: ExtractionServiceClient,
    authorization: str | None,
) -> JSONResponse:
    payload: dict[str, Any] | None = None
    if request.method in {"POST", "PATCH", "PUT"}:
        body = await request.body()
        if body:
            payload = await request.json()
    client_ip = request.client.host if request.client else None
    try:
        upstream = await extraction_service.call(
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
        raise HTTPException(status_code=503, detail="extraction-service unavailable") from exc
    return proxy_response(upstream)


@router.post("/documents/{document_id}/extract")
async def request_document_extraction(
    document_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/documents/{document_id}", extraction_service, authorization)


@router.get("/documents/{document_id}/extractions")
async def list_document_extractions(
    document_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/documents/{document_id}/jobs", extraction_service, authorization)


@router.get("/documents/{document_id}/extractions/latest")
async def get_latest_document_extraction(
    document_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/documents/{document_id}/latest", extraction_service, authorization)


@router.post("/documents/{document_id}/extract/reprocess")
async def reprocess_document_extraction(
    document_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/documents/{document_id}/reprocess", extraction_service, authorization)


@router.get("/extractions/jobs/{job_id}")
async def get_extraction_job(
    job_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/jobs/{job_id}", extraction_service, authorization)


@router.get("/extractions/jobs/{job_id}/status")
async def get_extraction_job_status(
    job_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/jobs/{job_id}/status", extraction_service, authorization)


@router.post("/extractions/jobs/{job_id}/retry")
async def retry_extraction_job(
    job_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/jobs/{job_id}/retry", extraction_service, authorization)


@router.post("/extractions/jobs/{job_id}/cancel")
async def cancel_extraction_job(
    job_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/jobs/{job_id}/cancel", extraction_service, authorization)


@router.get("/documents/{document_id}/extraction-result")
async def get_document_extraction_result(
    document_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/documents/{document_id}/result/latest", extraction_service, authorization)


@router.get("/extractions/jobs/{job_id}/result")
async def get_extraction_job_result(
    job_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/jobs/{job_id}/result", extraction_service, authorization)


@router.get("/extractions/results/{result_id}/fields")
async def list_extraction_result_fields(
    result_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/results/{result_id}/fields", extraction_service, authorization)


@router.get("/extractions/results/{result_id}/objects")
async def list_extraction_result_objects(
    result_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/results/{result_id}/objects", extraction_service, authorization)


@router.get("/extractions/results/{result_id}/array-items")
async def list_extraction_result_array_items(
    result_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/results/{result_id}/array-items", extraction_service, authorization)


@router.get("/extractions/fields/{field_value_id}/evidence")
async def list_extraction_field_evidence(
    field_value_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/fields/{field_value_id}/evidence", extraction_service, authorization)


@router.patch("/extractions/fields/{field_value_id}/correction")
async def correct_extraction_field(
    field_value_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/fields/{field_value_id}/correction", extraction_service, authorization)


@router.post("/extractions/fields/{field_value_id}/approve")
async def approve_extraction_field(
    field_value_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/fields/{field_value_id}/approve", extraction_service, authorization)


@router.post("/extractions/fields/{field_value_id}/reject")
async def reject_extraction_field(
    field_value_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/fields/{field_value_id}/reject", extraction_service, authorization)


@router.post("/extractions/results/{result_id}/approve")
async def approve_extraction_result(
    result_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/results/{result_id}/approve", extraction_service, authorization)


@router.post("/extractions/jobs/{job_id}/normalize/reprocess")
async def reprocess_extraction_normalization(
    job_id: str,
    request: Request,
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy(request, f"/extractions/jobs/{job_id}/normalize/reprocess", extraction_service, authorization)
