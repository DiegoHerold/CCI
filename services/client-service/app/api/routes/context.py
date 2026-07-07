from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.application.context import context_from_request
from app.application.schemas import (
    ClientContextResponse,
    ClientResponse,
    ContextClient,
    CurrentCompetence,
    IdentityUser,
    PreferenceResponse,
    PreferenceUpdate,
)
from app.application.services import PreferenceService
from app.config import Settings, get_settings
from app.dependencies import require_permission
from app.domain.enums import ClientStatus, Permission
from app.infrastructure.database.session import get_db
from app.infrastructure.identity_gateway import Principal
from app.infrastructure.repositories import ClientRepository, ClientUserRepository


router = APIRouter(prefix="/client-context", tags=["client-context"])
ContextReader = Annotated[
    Principal, Depends(require_permission(Permission.CONTEXT_READ))
]


@router.get("", response_model=ClientContextResponse)
def get_client_context(
    actor: ContextReader,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ClientContextResponse:
    clients, _ = ClientRepository(session).list_accessible(
        actor.id,
        actor.is_admin,
        status=ClientStatus.ACTIVE.value,
        page=1,
        limit=100,
        sort_by="name",
        sort_direction="asc",
    )
    bindings = ClientUserRepository(session)
    context_clients: list[ContextClient] = []
    for client in clients:
        binding = None if actor.is_admin else bindings.get(client.id, actor.id)
        context_clients.append(
            ContextClient(
                **ClientResponse.from_entity(client).model_dump(),
                user_client_role=binding.client_role if binding else None,
                responsibility_area=binding.responsibility_area if binding else None,
                is_primary_responsible=(
                    binding.is_primary_responsible if binding else None
                ),
            )
        )
    preference = PreferenceService(session, settings).get(actor.id)
    accessible_ids = {client.id for client in clients}
    default_client_id = (
        preference.default_client_id
        if preference and preference.default_client_id in accessible_ids
        else (clients[0].id if clients else None)
    )
    today = date.today()
    current_period = (
        preference.default_competence_period
        if preference
        and preference.default_client_id == default_client_id
        and preference.default_competence_period
        else f"{today.year:04d}-{today.month:02d}"
    )
    year, month = map(int, current_period.split("-"))
    return ClientContextResponse(
        user=IdentityUser(
            id=actor.id,
            name=actor.name,
            email=actor.email,
            status=actor.status,
            roles=list(actor.roles),
            permissions=list(actor.permissions),
        ),
        clients=context_clients,
        default_client_id=default_client_id,
        current_competence=CurrentCompetence(
            period=current_period, year=year, month=month
        ),
    )


@router.get("/preferences", response_model=PreferenceResponse)
def get_preferences(
    actor: ContextReader,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PreferenceResponse:
    return PreferenceResponse.from_entity(
        PreferenceService(session, settings).get(actor.id)
    )


@router.patch("/preferences", response_model=PreferenceResponse)
def update_preferences(
    request: Request,
    payload: PreferenceUpdate,
    actor: ContextReader,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PreferenceResponse:
    return PreferenceResponse.from_entity(
        PreferenceService(session, settings).update(
            payload, actor, context_from_request(request)
        )
    )

