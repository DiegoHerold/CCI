from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.cnpj import format_cnpj, is_valid_cnpj, normalize_cnpj
from app.domain.enums import (
    ClientRole,
    ClientStatus,
    CompetencyStatus,
    LinkStatus,
    ResponsibilityArea,
    TaxRegime,
)
from app.domain.folders import validate_folder_pattern
from app.infrastructure.database.models import (
    Client,
    ClientCompetency,
    ClientUser,
    UserClientPreference,
)


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        from_attributes=True,
    )


class IdentityUser(ApiModel):
    id: str
    name: str
    email: str
    status: str
    roles: list[str]
    permissions: list[str]


def _strip_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class ClientFields(ApiModel):
    code: str | None = Field(default=None, max_length=64)
    trade_name: str | None = Field(default=None, max_length=255)
    tax_regime: TaxRegime | None = None
    state_registration: str | None = Field(default=None, max_length=64)
    municipal_registration: str | None = Field(default=None, max_length=64)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, min_length=2, max_length=2)
    default_folder_path: str | None = Field(default=None, max_length=1024)
    competence_folder_pattern: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator(
        "code",
        "trade_name",
        "state_registration",
        "municipal_registration",
        "city",
        "default_folder_path",
        "notes",
    )
    @classmethod
    def strip_optional_fields(cls, value: str | None) -> str | None:
        return _strip_optional(value)

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().upper()
        valid = {
            "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
            "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
            "RS", "RO", "RR", "SC", "SP", "SE", "TO",
        }
        if value not in valid:
            raise ValueError("invalid Brazilian state")
        return value

    @field_validator("default_folder_path")
    @classmethod
    def validate_root_path(cls, value: str | None) -> str | None:
        if value is not None and "\x00" in value:
            raise ValueError("invalid folder path")
        return value

    @field_validator("competence_folder_pattern")
    @classmethod
    def validate_pattern(cls, value: str | None) -> str | None:
        return validate_folder_pattern(value) if value is not None else None


class ClientCreate(ClientFields):
    name: str = Field(min_length=2, max_length=255)
    cnpj: str = Field(min_length=1, max_length=32)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("name is required")
        return value

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, value: str) -> str:
        if not is_valid_cnpj(value):
            raise ValueError("CNPJ inválido")
        return value.strip()


class ClientUpdate(ClientFields):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    cnpj: str | None = Field(default=None, min_length=1, max_length=32)

    @field_validator("name")
    @classmethod
    def strip_update_name(cls, value: str | None) -> str | None:
        return _strip_optional(value)

    @field_validator("cnpj")
    @classmethod
    def validate_update_cnpj(cls, value: str | None) -> str | None:
        if value is not None and not is_valid_cnpj(value):
            raise ValueError("CNPJ inválido")
        return value.strip() if value is not None else None

    @model_validator(mode="after")
    def require_change(self) -> "ClientUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        return self


class ClientResponse(ApiModel):
    id: str
    code: str | None
    name: str
    trade_name: str | None
    cnpj: str
    cnpj_normalized: str
    status: ClientStatus
    tax_regime: TaxRegime | None
    state_registration: str | None
    municipal_registration: str | None
    city: str | None
    state: str | None
    default_folder_path: str | None
    competence_folder_pattern: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
    disabled_at: datetime | None
    archived_at: datetime | None

    @classmethod
    def from_entity(cls, entity: Client) -> "ClientResponse":
        return cls.model_validate(entity)


class ClientListResponse(ApiModel):
    items: list[ClientResponse]
    page: int
    limit: int
    total: int


class FolderUpdate(ApiModel):
    default_folder_path: str | None = Field(default=None, max_length=1024)
    competence_folder_pattern: str | None = Field(default=None, max_length=255)

    @field_validator("default_folder_path")
    @classmethod
    def clean_path(cls, value: str | None) -> str | None:
        value = _strip_optional(value)
        if value is not None and ("\x00" in value or ".." in value.split("/") or ".." in value.split("\\")):
            raise ValueError("unsafe folder path")
        return value

    @field_validator("competence_folder_pattern")
    @classmethod
    def clean_pattern(cls, value: str | None) -> str | None:
        return validate_folder_pattern(value) if value is not None else None

    @model_validator(mode="after")
    def require_change(self) -> "FolderUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        return self


class FolderResponse(ApiModel):
    client_id: str
    default_folder_path: str | None
    competence_folder_pattern: str


class PeriodPayload(ApiModel):
    year: int = Field(ge=1900, le=2200)
    month: int = Field(ge=1, le=12)


class EnsureCurrentPayload(ApiModel):
    year: int | None = Field(default=None, ge=1900, le=2200)
    month: int | None = Field(default=None, ge=1, le=12)

    @model_validator(mode="after")
    def both_or_neither(self) -> "EnsureCurrentPayload":
        if (self.year is None) != (self.month is None):
            raise ValueError("year and month must be provided together")
        return self


class FolderPreviewResponse(FolderResponse):
    period: str
    resolved_competence_path: str


class CompetencyCreate(PeriodPayload):
    status: CompetencyStatus = CompetencyStatus.OPEN


class CompetencyUpdate(ApiModel):
    folder_path: str | None = Field(default=None, max_length=1024)

    @field_validator("folder_path")
    @classmethod
    def clean_folder_path(cls, value: str | None) -> str | None:
        return _strip_optional(value)

    @model_validator(mode="after")
    def require_change(self) -> "CompetencyUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        return self


class CompetencyStatusUpdate(ApiModel):
    status: CompetencyStatus


class CompetencyResponse(ApiModel):
    id: str
    client_id: str
    period: str
    year: int
    month: int
    status: CompetencyStatus
    folder_path: str | None
    folder_resolved_at: datetime | None
    created_by_user_id: str
    closed_by_user_id: str | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    archived_at: datetime | None
    created: bool | None = None

    @classmethod
    def from_entity(
        cls, entity: ClientCompetency, created: bool | None = None
    ) -> "CompetencyResponse":
        result = cls.model_validate(entity)
        result.created = created
        return result


class CompetencyListResponse(ApiModel):
    items: list[CompetencyResponse]
    page: int
    limit: int
    total: int


class ClientUserCreate(ApiModel):
    user_id: str = Field(min_length=1, max_length=36)
    client_role: ClientRole
    responsibility_area: ResponsibilityArea = ResponsibilityArea.GENERAL
    is_primary_responsible: bool = False


class ClientUserUpdate(ApiModel):
    client_role: ClientRole | None = None
    responsibility_area: ResponsibilityArea | None = None
    is_primary_responsible: bool | None = None
    status: LinkStatus | None = None

    @model_validator(mode="after")
    def require_change(self) -> "ClientUserUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        return self


class ClientUserResponse(ApiModel):
    id: str
    client_id: str
    user_id: str
    client_role: ClientRole
    status: LinkStatus
    is_primary_responsible: bool
    responsibility_area: ResponsibilityArea
    created_at: datetime
    updated_at: datetime
    disabled_at: datetime | None

    @classmethod
    def from_entity(cls, entity: ClientUser) -> "ClientUserResponse":
        return cls.model_validate(entity)


class ClientUserListResponse(ApiModel):
    items: list[ClientUserResponse]
    page: int
    limit: int
    total: int


class PreferenceUpdate(ApiModel):
    default_client_id: str | None = Field(default=None, max_length=36)
    default_competence_period: str | None = Field(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$")

    @model_validator(mode="after")
    def require_change(self) -> "PreferenceUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        if self.default_competence_period and not self.default_client_id:
            raise ValueError("defaultClientId is required with a competence")
        return self


class PreferenceResponse(ApiModel):
    default_client_id: str | None = None
    default_competence_period: str | None = None

    @classmethod
    def from_entity(
        cls, entity: UserClientPreference | None
    ) -> "PreferenceResponse":
        if entity is None:
            return cls()
        return cls.model_validate(entity)


class ContextClient(ClientResponse):
    user_client_role: ClientRole | None = None
    responsibility_area: ResponsibilityArea | None = None
    is_primary_responsible: bool | None = None


class CurrentCompetence(ApiModel):
    period: str
    year: int
    month: int


class ClientContextResponse(ApiModel):
    user: IdentityUser
    clients: list[ContextClient]
    default_client_id: str | None
    current_competence: CurrentCompetence
