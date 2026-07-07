from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Role(str, Enum):
    ADMIN = "admin"
    COORDINATOR = "coordinator"
    ANALYST = "analyst"
    REVIEWER = "reviewer"
    READ_ONLY = "read_only"


class CompetenceStatus(str, Enum):
    WAITING_DOCUMENTS = "waiting_documents"
    DOCUMENTS_IMPORTED = "documents_imported"
    DOCUMENTS_MAPPED = "documents_mapped"
    EXTRACTING = "extracting"
    VARIABLES_READY = "variables_ready"
    EXECUTING = "executing"
    FINISHED = "finished"
    BLOCKED = "blocked"
    ERROR = "error"


class DocumentType(str, Enum):
    BALANCETE = "balancete"
    GUIA_INSS = "guia_inss"
    GUIA_FGTS = "guia_fgts"
    FOLHA_PAGAMENTO = "folha_pagamento"
    RELATORIO_FISCAL = "relatorio_fiscal"
    RELATORIO_CONTABIL = "relatorio_contabil"
    EXTRATO = "extrato"
    OUTRO = "outro"
    DESCONHECIDO = "desconhecido"


class DocumentStatus(str, Enum):
    IMPORTED = "imported"
    CLASSIFIED = "classified"
    AMBIGUOUS = "ambiguous"
    MISSING = "missing"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    EXTRACTED = "extracted"
    ERROR = "error"


class VariableStatus(str, Enum):
    EXTRACTED = "extracted"
    NORMALIZED = "normalized"
    CONFIRMED = "confirmed"
    CORRECTED = "corrected"
    IGNORED = "ignored"
    NEED_REVIEW = "need_review"
    USED_IN_RULE = "used_in_rule"


class RuleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResultStatus(str, Enum):
    APPROVED = "approved"
    DIVERGENT = "divergent"
    ERROR = "error"
    PENDING = "pending"
    NOT_APPLICABLE = "not_applicable"
    NEEDS_REVIEW = "needs_review"


class ReportStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    GENERATED = "generated"
    FAILED = "failed"


class Permission(BaseModel):
    name: str


class User(BaseModel):
    user_id: str
    email: str
    name: str
    roles: list[Role] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    active: bool = True


class Client(BaseModel):
    client_id: str
    name: str
    cnpj: str | None = None


class Competence(BaseModel):
    competence_id: str
    client_id: str
    reference: str
    status: CompetenceStatus


class Document(BaseModel):
    document_id: str
    client_id: str
    competence_id: str
    filename: str
    document_type: DocumentType
    status: DocumentStatus


class Variable(BaseModel):
    variable_id: str
    key: str
    value: Any
    status: VariableStatus


class Rule(BaseModel):
    rule_id: str
    name: str
    version: int = Field(ge=1)
    status: RuleStatus
    logic: dict[str, Any]


class Execution(BaseModel):
    execution_id: str
    client_id: str
    competence_id: str
    status: ExecutionStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None


class Result(BaseModel):
    result_id: str
    execution_id: str
    rule_id: str
    status: ResultStatus
    message: str | None = None


class AuditEntry(BaseModel):
    audit_id: str
    action: str
    occurred_at: datetime
    actor_id: str
    details: dict[str, Any] = Field(default_factory=dict)


class Report(BaseModel):
    report_id: str
    execution_id: str
    format: str
    status: ReportStatus
    storage_key: str | None = None


class EventEnvelope(BaseModel):
    event_id: str
    event_type: str
    version: int = Field(ge=1)
    occurred_at: datetime
    correlation_id: str
    producer: str
    payload: dict[str, Any]
