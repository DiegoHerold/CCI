from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.schemas import (
    TemplateMatchConfirmRequest,
    TemplateMatchingRequest,
    TemplateMatchingRunListResponse,
    TemplateMatchingRunResponse,
)
from app.dependencies import get_template_matching_service
from app.modules.matching.application.service import TemplateMatchingService
from app.modules.matching.public.commands import ConfirmTemplateMatchCommand, MatchDocumentCommand


router = APIRouter(prefix="/template-matching", tags=["template-matching"])


@router.post("/documents/{document_id}/match", response_model=TemplateMatchingRunResponse)
async def match_document(
    document_id: str,
    payload: TemplateMatchingRequest,
    service: Annotated[TemplateMatchingService, Depends(get_template_matching_service)],
) -> TemplateMatchingRunResponse:
    run = await service.match_document(
        MatchDocumentCommand(
            document_id=document_id,
            force_reprocess=payload.force_reprocess,
            category_hint=payload.category_hint,
            max_candidates=payload.max_candidates,
        )
    )
    return TemplateMatchingRunResponse.from_entity(run)


@router.get("/documents/{document_id}", response_model=TemplateMatchingRunResponse)
def get_latest_document_match(
    document_id: str,
    service: Annotated[TemplateMatchingService, Depends(get_template_matching_service)],
) -> TemplateMatchingRunResponse:
    return TemplateMatchingRunResponse.from_entity(service.get_latest_for_document(document_id))


@router.get("/documents/{document_id}/runs", response_model=TemplateMatchingRunListResponse)
def list_document_matching_runs(
    document_id: str,
    service: Annotated[TemplateMatchingService, Depends(get_template_matching_service)],
) -> TemplateMatchingRunListResponse:
    return TemplateMatchingRunListResponse(
        items=[TemplateMatchingRunResponse.from_entity(run) for run in service.list_runs_for_document(document_id)]
    )


@router.get("/runs/{matching_run_id}", response_model=TemplateMatchingRunResponse)
def get_matching_run(
    matching_run_id: str,
    service: Annotated[TemplateMatchingService, Depends(get_template_matching_service)],
) -> TemplateMatchingRunResponse:
    return TemplateMatchingRunResponse.from_entity(service.get_run(matching_run_id))


@router.post("/documents/{document_id}/confirm", response_model=TemplateMatchingRunResponse)
def confirm_document_match(
    document_id: str,
    payload: TemplateMatchConfirmRequest,
    service: Annotated[TemplateMatchingService, Depends(get_template_matching_service)],
) -> TemplateMatchingRunResponse:
    run = service.confirm_match(
        ConfirmTemplateMatchCommand(
            document_id=document_id,
            template_id=payload.template_id,
            template_version_id=payload.template_version_id,
            reason=payload.reason,
        )
    )
    return TemplateMatchingRunResponse.from_entity(run)
