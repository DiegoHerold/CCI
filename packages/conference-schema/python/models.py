from datetime import datetime

from pydantic import BaseModel, Field


class ExpectedDocument(BaseModel):
    category: str
    template_id: str | None = None
    required: bool = True


class ConferenceResult(BaseModel):
    status: str
    approved_count: int = Field(ge=0)
    divergent_count: int = Field(ge=0)


class TimelineEvent(BaseModel):
    event_type: str
    occurred_at: datetime
    actor_id: str | None = None
    correlation_id: str
    details: dict = Field(default_factory=dict)


class ConferenceExecution(BaseModel):
    execution_id: str
    model_id: str
    client_id: str
    competence_id: str
    status: str
    expected_documents: list[ExpectedDocument] = Field(default_factory=list)
    rule_versions: list[dict] = Field(default_factory=list)
    result: ConferenceResult | None = None
    timeline: list[TimelineEvent] = Field(default_factory=list)
