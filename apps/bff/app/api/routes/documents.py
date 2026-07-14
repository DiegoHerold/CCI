from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.routes.auth import proxy_response
from app.dependencies import get_document_service_client, get_extraction_service_client, get_template_service_client
from app.infrastructure.clients.document_service_client import DocumentServiceClient
from app.infrastructure.clients.extraction_service_client import ExtractionServiceClient
from app.infrastructure.clients.template_service_client import TemplateServiceClient


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


async def _safe_call(client: Any, method: str, path: str, request: Request, authorization: str | None):
    try:
        upstream = await client.call(
            method,
            path,
            request.state.correlation_id,
            authorization=authorization,
            params=list(request.query_params.multi_items()) if method == "GET" else None,
        )
    except httpx.RequestError:
        return {"status_code": 503, "payload": None}
    if upstream.status_code == 404:
        return {"status_code": 404, "payload": None}
    if upstream.status_code >= 400:
        return {"status_code": upstream.status_code, "payload": upstream.payload}
    return {"status_code": upstream.status_code, "payload": upstream.payload}


def _preview_summary(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {"status": "not_started", "requires_ocr": False}
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    return {
        "status": payload.get("status") or metadata.get("status") or "preview_ready",
        "requires_ocr": bool(metadata.get("requiresOcr") or metadata.get("requires_ocr") or payload.get("requiresOcr") or payload.get("requires_ocr")),
    }


def _best_candidate(match: dict[str, Any] | None) -> dict[str, Any] | None:
    candidates = match.get("candidates") if isinstance(match, dict) else None
    if isinstance(candidates, list) and candidates:
        return candidates[0]
    return None


def _next_action(document: dict[str, Any], preview: dict[str, Any], match: dict[str, Any] | None, extraction: dict[str, Any] | None, result: dict[str, Any] | None) -> dict[str, str]:
    preview_status = preview.get("status")
    match_status = match.get("status") if isinstance(match, dict) else "not_started"
    extraction_status = extraction.get("status") if isinstance(extraction, dict) else "not_started"
    result_status = result.get("status") if isinstance(result, dict) else None
    if preview_status not in {"preview_ready", "ready"}:
        return {"type": "request_preview", "label": "Ler documento"}
    if match_status in {None, "not_started"}:
        return {"type": "run_template_match", "label": "Identificar template"}
    if match_status == "not_found":
        return {"type": "create_template", "label": "Criar template a partir deste documento"}
    if match_status == "ambiguous":
        return {"type": "choose_template", "label": "Escolher template"}
    if match_status == "matched" and not match.get("manualOverride"):
        return {"type": "confirm_template", "label": "Confirmar template"}
    if extraction_status in {"not_started", None}:
        return {"type": "start_extraction", "label": "Extrair variaveis"}
    if extraction_status in {"queued", "starting", "running", "waiting_worker", "worker_running", "retrying"}:
        return {"type": "wait_extraction", "label": "Acompanhar extracao"}
    if result_status == "requires_review" or extraction_status == "requires_review":
        return {"type": "review_variables", "label": "Revisar variaveis"}
    if result_status in {"completed", "completed_with_warnings"}:
        return {"type": "view_result", "label": "Ver variaveis"}
    if extraction_status == "failed":
        return {"type": "reprocess", "label": "Tentar novamente"}
    return {"type": "open_document", "label": "Abrir documento"}


@router.get("/documents/{document_id}/flow-state")
async def document_flow_state(
    document_id: str,
    request: Request,
    document_service: Annotated[DocumentServiceClient, Depends(get_document_service_client)],
    template_service: Annotated[TemplateServiceClient, Depends(get_template_service_client)],
    extraction_service: Annotated[ExtractionServiceClient, Depends(get_extraction_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    document_response = await _safe_call(document_service, "GET", f"/documents/{document_id}", request, authorization)
    if document_response["status_code"] == 404:
        raise HTTPException(status_code=404, detail="document not found")
    if document_response["status_code"] >= 500:
        raise HTTPException(status_code=503, detail="document-service unavailable")
    document = document_response["payload"] or {}
    preview_response = await _safe_call(document_service, "GET", f"/documents/{document_id}/preview", request, authorization)
    match_response = await _safe_call(template_service, "GET", f"/template-matching/documents/{document_id}", request, authorization)
    extraction_response = await _safe_call(extraction_service, "GET", f"/extractions/documents/{document_id}/latest", request, authorization)
    result_response = await _safe_call(extraction_service, "GET", f"/extractions/documents/{document_id}/result/latest", request, authorization)

    preview = _preview_summary(preview_response["payload"] if preview_response["status_code"] < 400 else None)
    match = match_response["payload"] if match_response["status_code"] < 400 else None
    extraction = extraction_response["payload"] if extraction_response["status_code"] < 400 else None
    result = result_response["payload"] if result_response["status_code"] < 400 else None
    next_action = _next_action(document, preview, match, extraction, result)
    payload = {
        "document": {
            "document_id": document.get("documentId") or document.get("document_id") or document_id,
            "filename": document.get("originalFilename") or document.get("filename"),
            "status": document.get("status"),
            "file_format": document.get("fileFormat") or document.get("file_format"),
            "client_id": document.get("clientId") or document.get("client_id"),
            "competence_id": document.get("competenceId") or document.get("competence_id"),
        },
        "preview": preview,
        "template_matching": {
            "status": match.get("status") if isinstance(match, dict) else "not_started",
            "confidence": match.get("confidence") if isinstance(match, dict) else 0,
            "best_candidate": _best_candidate(match),
            "candidates": match.get("candidates", []) if isinstance(match, dict) else [],
            "matching_run_id": match.get("matchingRunId") or match.get("matching_run_id") if isinstance(match, dict) else None,
            "manual_override": bool(match.get("manualOverride") or match.get("manual_override")) if isinstance(match, dict) else False,
        },
        "template": {
            "template_id": (match or {}).get("matchedTemplateId") or (match or {}).get("matched_template_id"),
            "template_version_id": (match or {}).get("matchedTemplateVersionId") or (match or {}).get("matched_template_version_id"),
            "status": "confirmed" if isinstance(match, dict) and match.get("manualOverride") else ((match or {}).get("status")),
        },
        "extraction": {
            "job_id": (extraction or {}).get("extractionJobId") or (extraction or {}).get("extraction_job_id"),
            "status": (extraction or {}).get("status") or "not_started",
            "error_message": (extraction or {}).get("errorMessage") or (extraction or {}).get("error_message"),
        },
        "normalization": {
            "status": (result or {}).get("status") or "not_started",
        },
        "result": {
            "result_id": (result or {}).get("extractionResultId") or (result or {}).get("extraction_result_id"),
            "status": (result or {}).get("status"),
            "field_count": (result or {}).get("fieldCount") or (result or {}).get("field_count") or 0,
            "requires_review_count": (result or {}).get("requiresReviewCount") or (result or {}).get("requires_review_count") or 0,
            "normalized_count": (result or {}).get("normalizedCount") or (result or {}).get("normalized_count") or 0,
        },
        "next_action": next_action,
    }
    return JSONResponse(content=payload)


@router.api_route("/documents/{path:path}", methods=["GET", "POST", "PATCH"])
async def documents_nested(
    path: str,
    request: Request,
    document_service: Annotated[DocumentServiceClient, Depends(get_document_service_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    return await _proxy_json(request, f"/documents/{path}", document_service, authorization)
