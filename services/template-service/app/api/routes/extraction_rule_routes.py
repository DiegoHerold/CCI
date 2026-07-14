from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.application.schemas import (
    ExtractionRuleCreate,
    ExtractionRuleListResponse,
    ExtractionRuleResponse,
    ExtractionRuleUpdate,
)
from app.application.services import TemplateService
from app.dependencies import get_template_service


router = APIRouter(tags=["template-extraction-rules"])
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]


@router.post("/templates/{template_id}/extraction-rules", response_model=ExtractionRuleResponse, status_code=201)
def create_rule(template_id: str, payload: ExtractionRuleCreate, service: TemplateServiceDep) -> ExtractionRuleResponse:
    return ExtractionRuleResponse.from_entity(service.create_rule(template_id, payload))


@router.get("/templates/{template_id}/extraction-rules", response_model=ExtractionRuleListResponse)
def list_rules(template_id: str, service: TemplateServiceDep) -> ExtractionRuleListResponse:
    return ExtractionRuleListResponse(
        items=[ExtractionRuleResponse.from_entity(item) for item in service.list_rules(template_id)]
    )


@router.patch("/templates/{template_id}/extraction-rules/{rule_id}", response_model=ExtractionRuleResponse)
def update_rule(
    template_id: str, rule_id: str, payload: ExtractionRuleUpdate, service: TemplateServiceDep
) -> ExtractionRuleResponse:
    return ExtractionRuleResponse.from_entity(service.update_rule(template_id, rule_id, payload))


@router.delete("/templates/{template_id}/extraction-rules/{rule_id}", status_code=204)
def delete_rule(template_id: str, rule_id: str, service: TemplateServiceDep) -> Response:
    service.delete_rule(template_id, rule_id)
    return Response(status_code=204)
