from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExtractRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    extraction_job_id: str
    correlation_id: str | None = None
    document: dict[str, Any]
    preview: dict[str, Any]
    template: dict[str, Any]
    options: dict[str, Any] = Field(default_factory=dict)


class ExtractResponse(BaseModel):
    extraction_job_id: str
    status: str
    raw_output: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
