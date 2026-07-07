from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.application.context import context_from_request
from app.application.schemas import (
    ClientCreate,
    ClientListResponse,
    ClientResponse,
    ClientUpdate,
    ClientUserCreate,
    ClientUserListResponse,
    ClientUserResponse,
    ClientUserUpdate,
    CompetencyCreate,
    CompetencyListResponse,
    CompetencyResponse,
    CompetencyStatusUpdate,
    CompetencyUpdate,
    EnsureCurrentPayload,
    FolderPreviewResponse,
    FolderResponse,
    FolderUpdate,
    PeriodPayload,
)
from app.application.services import ClientService, ClientUserService, CompetencyService
from app.config import Settings, get_settings
from app.dependencies import (
    ClientAccess,
    CurrentPrincipal,
    get_identity_gateway,
    require_permission,
)
from app.domain.cnpj import normalize_cnpj
from app.domain.enums import (
    ClientRole,
    ClientStatus,
    CompetencyStatus,
    LinkStatus,
    Permission,
    ResponsibilityArea,
    TaxRegime,
)
from app.errors import BusinessRuleError
from app.infrastructure.database.models import ClientUser
from app.infrastructure.database.session import get_db
from app.infrastructure.identity_gateway import IdentityGateway, Principal
from app.infrastructure.repositories import ClientRepository, ClientUserRepository, CompetencyRepository


router = APIRouter(prefix="/clients", tags=["clients"])


def permitted(permission: str):
    return Annotated[Principal, Depends(require_permission(permission))]


@router.get("", response_model=ClientListResponse)
def list_clients(
    actor: permitted(Permission.CLIENTS_READ),
    session: Annotated[Session, Depends(get_db)],
    status_filter: Annotated[ClientStatus | None, Query(alias="status")] = None,
    search: str | None = None,
    cnpj: str | None = None,
    city: str | None = None,
    state: str | None = None,
    tax_regime: Annotated[TaxRegime | None, Query(alias="taxRegime")] = None,
    responsibility_area: Annotated[ResponsibilityArea | None, Query(alias="responsibilityArea")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    sort_by: Annotated[
        Literal["name", "tradeName", "code", "cnpj", "status", "createdAt", "updatedAt"],
        Query(alias="sortBy"),
    ] = "name",
    sort_direction: Annotated[Literal["asc", "desc"], Query(alias="sortDirection")] = "asc",
) -> ClientListResponse:
    items, total = ClientRepository(session).list_accessible(
        actor.id,
        actor.is_admin,
        status=status_filter.value if status_filter else None,
        search=search,
        cnpj=normalize_cnpj(cnpj) if cnpj else None,
        city=city,
        state=state,
        tax_regime=tax_regime.value if tax_regime else None,
        responsibility_area=responsibility_area.value if responsibility_area else None,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )
    return ClientListResponse(
        items=[ClientResponse.from_entity(item) for item in items],
        page=page,
        limit=limit,
        total=total,
    )


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    request: Request,
    payload: ClientCreate,
    actor: permitted(Permission.CLIENTS_CREATE),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ClientResponse:
    entity = ClientService(session, settings).create(
        payload, actor, context_from_request(request)
    )
    return ClientResponse.from_entity(entity)


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: str,
    _: ClientAccess,
    actor: permitted(Permission.CLIENTS_READ),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ClientResponse:
    return ClientResponse.from_entity(ClientService(session, settings).get(client_id))


@router.patch("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: str,
    request: Request,
    payload: ClientUpdate,
    _: ClientAccess,
    actor: permitted(Permission.CLIENTS_UPDATE),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ClientResponse:
    return ClientResponse.from_entity(
        ClientService(session, settings).update(
            client_id, payload, actor, context_from_request(request)
        )
    )


def _status_change(
    client_id: str,
    target: ClientStatus,
    request: Request,
    actor: Principal,
    session: Session,
    settings: Settings,
) -> ClientResponse:
    return ClientResponse.from_entity(
        ClientService(session, settings).change_status(
            client_id, target, actor, context_from_request(request)
        )
    )


@router.patch("/{client_id}/disable", response_model=ClientResponse)
def disable_client(
    client_id: str,
    request: Request,
    _: ClientAccess,
    actor: permitted(Permission.CLIENTS_DISABLE),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ClientResponse:
    return _status_change(client_id, ClientStatus.INACTIVE, request, actor, session, settings)


@router.patch("/{client_id}/archive", response_model=ClientResponse)
def archive_client(
    client_id: str,
    request: Request,
    _: ClientAccess,
    actor: permitted(Permission.CLIENTS_ARCHIVE),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ClientResponse:
    return _status_change(client_id, ClientStatus.ARCHIVED, request, actor, session, settings)


@router.patch("/{client_id}/restore", response_model=ClientResponse)
def restore_client(
    client_id: str,
    request: Request,
    _: ClientAccess,
    actor: permitted(Permission.CLIENTS_ARCHIVE),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ClientResponse:
    return _status_change(client_id, ClientStatus.ACTIVE, request, actor, session, settings)


@router.get("/{client_id}/folder", response_model=FolderResponse)
def get_folder(
    client_id: str,
    _: ClientAccess,
    actor: permitted(Permission.FOLDERS_READ),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> FolderResponse:
    client = ClientService(session, settings).get(client_id)
    return FolderResponse(
        client_id=client.id,
        default_folder_path=client.default_folder_path,
        competence_folder_pattern=client.competence_folder_pattern,
    )


@router.patch("/{client_id}/folder", response_model=FolderResponse)
def update_folder(
    client_id: str,
    request: Request,
    payload: FolderUpdate,
    _: ClientAccess,
    actor: permitted(Permission.FOLDERS_UPDATE),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> FolderResponse:
    client = ClientService(session, settings).update_folder(
        client_id, payload, actor, context_from_request(request)
    )
    return FolderResponse(
        client_id=client.id,
        default_folder_path=client.default_folder_path,
        competence_folder_pattern=client.competence_folder_pattern,
    )


@router.post("/{client_id}/folder-preview", response_model=FolderPreviewResponse)
def preview_folder(
    client_id: str,
    request: Request,
    payload: PeriodPayload,
    _: ClientAccess,
    actor: permitted(Permission.FOLDERS_PREVIEW),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> FolderPreviewResponse:
    client, path = ClientService(session, settings).preview_folder(
        client_id, payload.year, payload.month, actor, context_from_request(request)
    )
    return FolderPreviewResponse(
        client_id=client.id,
        period=f"{payload.year:04d}-{payload.month:02d}",
        default_folder_path=client.default_folder_path,
        competence_folder_pattern=client.competence_folder_pattern,
        resolved_competence_path=path,
    )


@router.get("/{client_id}/competencies", response_model=CompetencyListResponse)
def list_competencies(
    client_id: str,
    _: ClientAccess,
    actor: permitted(Permission.COMPETENCIES_READ),
    session: Annotated[Session, Depends(get_db)],
    status_filter: Annotated[CompetencyStatus | None, Query(alias="status")] = None,
    year: int | None = Query(default=None, ge=1900, le=2200),
    from_period: Annotated[str | None, Query(alias="fromPeriod", pattern=r"^\d{4}-(0[1-9]|1[0-2])$")] = None,
    to_period: Annotated[str | None, Query(alias="toPeriod", pattern=r"^\d{4}-(0[1-9]|1[0-2])$")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> CompetencyListResponse:
    items, total = CompetencyRepository(session).list(
        client_id,
        status=status_filter.value if status_filter else None,
        year=year,
        from_period=from_period,
        to_period=to_period,
        page=page,
        limit=limit,
    )
    return CompetencyListResponse(
        items=[CompetencyResponse.from_entity(item) for item in items],
        page=page,
        limit=limit,
        total=total,
    )


@router.post("/{client_id}/competencies", response_model=CompetencyResponse, status_code=status.HTTP_201_CREATED)
def create_competency(
    client_id: str,
    request: Request,
    payload: CompetencyCreate,
    _: ClientAccess,
    actor: permitted(Permission.COMPETENCIES_CREATE),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CompetencyResponse:
    entity = CompetencyService(session, settings).create(
        client_id, payload, actor, context_from_request(request)
    )
    return CompetencyResponse.from_entity(entity)


@router.post("/{client_id}/competencies/ensure-current", response_model=CompetencyResponse)
def ensure_current_competency(
    client_id: str,
    request: Request,
    payload: EnsureCurrentPayload | None,
    _: ClientAccess,
    actor: permitted(Permission.COMPETENCIES_CREATE),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CompetencyResponse:
    payload = payload or EnsureCurrentPayload()
    entity, created = CompetencyService(session, settings).ensure_current(
        client_id, payload.year, payload.month, actor, context_from_request(request)
    )
    return CompetencyResponse.from_entity(entity, created=created)


@router.get("/{client_id}/competencies/{competency_id}", response_model=CompetencyResponse)
def get_competency(
    client_id: str,
    competency_id: str,
    _: ClientAccess,
    actor: permitted(Permission.COMPETENCIES_READ),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CompetencyResponse:
    return CompetencyResponse.from_entity(
        CompetencyService(session, settings).get(client_id, competency_id)
    )


@router.patch("/{client_id}/competencies/{competency_id}", response_model=CompetencyResponse)
def update_competency(
    client_id: str,
    competency_id: str,
    request: Request,
    payload: CompetencyUpdate,
    _: ClientAccess,
    actor: permitted(Permission.COMPETENCIES_UPDATE),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CompetencyResponse:
    return CompetencyResponse.from_entity(
        CompetencyService(session, settings).update(
            client_id, competency_id, payload, actor, context_from_request(request)
        )
    )


@router.patch("/{client_id}/competencies/{competency_id}/status", response_model=CompetencyResponse)
def update_competency_status(
    client_id: str,
    competency_id: str,
    request: Request,
    payload: CompetencyStatusUpdate,
    _: ClientAccess,
    actor: permitted(Permission.COMPETENCIES_UPDATE),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CompetencyResponse:
    return CompetencyResponse.from_entity(
        CompetencyService(session, settings).change_status(
            client_id, competency_id, payload.status, actor, context_from_request(request)
        )
    )


@router.patch("/{client_id}/competencies/{competency_id}/close", response_model=CompetencyResponse)
def close_competency(
    client_id: str,
    competency_id: str,
    request: Request,
    _: ClientAccess,
    actor: permitted(Permission.COMPETENCIES_CLOSE),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CompetencyResponse:
    return CompetencyResponse.from_entity(
        CompetencyService(session, settings).close(
            client_id, competency_id, actor, context_from_request(request)
        )
    )


@router.patch("/{client_id}/competencies/{competency_id}/archive", response_model=CompetencyResponse)
def archive_competency(
    client_id: str,
    competency_id: str,
    request: Request,
    _: ClientAccess,
    actor: permitted(Permission.COMPETENCIES_ARCHIVE),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CompetencyResponse:
    return CompetencyResponse.from_entity(
        CompetencyService(session, settings).change_status(
            client_id, competency_id, CompetencyStatus.ARCHIVED, actor, context_from_request(request)
        )
    )


@router.get("/{client_id}/users", response_model=ClientUserListResponse)
def list_client_users(
    client_id: str,
    _: ClientAccess,
    actor: permitted(Permission.CLIENT_USERS_READ),
    session: Annotated[Session, Depends(get_db)],
    status_filter: Annotated[LinkStatus | None, Query(alias="status")] = None,
    client_role: Annotated[ClientRole | None, Query(alias="clientRole")] = None,
    responsibility_area: Annotated[ResponsibilityArea | None, Query(alias="responsibilityArea")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ClientUserListResponse:
    items, total = ClientUserRepository(session).list(
        client_id,
        status=status_filter.value if status_filter else None,
        client_role=client_role.value if client_role else None,
        responsibility_area=responsibility_area.value if responsibility_area else None,
        page=page,
        limit=limit,
    )
    return ClientUserListResponse(
        items=[ClientUserResponse.from_entity(item) for item in items],
        page=page,
        limit=limit,
        total=total,
    )


@router.post("/{client_id}/users", response_model=ClientUserResponse, status_code=status.HTTP_201_CREATED)
async def link_client_user(
    client_id: str,
    request: Request,
    payload: ClientUserCreate,
    _: ClientAccess,
    actor: permitted(Permission.CLIENT_USERS_MANAGE),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    identity: Annotated[IdentityGateway, Depends(get_identity_gateway)],
) -> ClientUserResponse:
    target = await identity.get_user(
        payload.user_id, actor, getattr(request.state, "correlation_id", "system")
    )
    if target.get("status") != "ACTIVE":
        raise BusinessRuleError("IDENTITY_USER_INACTIVE", "Identity user must be active")
    entity = ClientUserService(session, settings).create(
        client_id, payload, actor, context_from_request(request)
    )
    return ClientUserResponse.from_entity(entity)


@router.get("/{client_id}/users/{user_id}", response_model=ClientUserResponse)
def get_client_user(
    client_id: str,
    user_id: str,
    _: ClientAccess,
    actor: permitted(Permission.CLIENT_USERS_READ),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ClientUserResponse:
    return ClientUserResponse.from_entity(
        ClientUserService(session, settings).get(client_id, user_id)
    )


@router.patch("/{client_id}/users/{user_id}", response_model=ClientUserResponse)
def update_client_user(
    client_id: str,
    user_id: str,
    request: Request,
    payload: ClientUserUpdate,
    _: ClientAccess,
    actor: permitted(Permission.CLIENT_USERS_MANAGE),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ClientUserResponse:
    return ClientUserResponse.from_entity(
        ClientUserService(session, settings).update(
            client_id, user_id, payload, actor, context_from_request(request)
        )
    )


@router.delete("/{client_id}/users/{user_id}", response_model=ClientUserResponse)
def unlink_client_user(
    client_id: str,
    user_id: str,
    request: Request,
    _: ClientAccess,
    actor: permitted(Permission.CLIENT_USERS_MANAGE),
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ClientUserResponse:
    return ClientUserResponse.from_entity(
        ClientUserService(session, settings).disable(
            client_id, user_id, actor, context_from_request(request)
        )
    )
