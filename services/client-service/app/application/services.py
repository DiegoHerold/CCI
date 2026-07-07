from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.context import RequestContext
from app.application.schemas import (
    ClientCreate,
    ClientUpdate,
    ClientUserCreate,
    ClientUserUpdate,
    CompetencyCreate,
    CompetencyUpdate,
    FolderUpdate,
    PreferenceUpdate,
)
from app.config import Settings
from app.domain.cnpj import format_cnpj, normalize_cnpj
from app.domain.enums import (
    AuditEventType,
    ClientStatus,
    CompetencyStatus,
    LinkStatus,
)
from app.domain.folders import resolve_competence_path
from app.errors import (
    BusinessRuleError,
    ClientAccessDeniedError,
    ConflictError,
    NotFoundError,
)
from app.infrastructure.database.models import (
    Client,
    ClientAuditEvent,
    ClientCompetency,
    ClientUser,
    UserClientPreference,
)
from app.infrastructure.identity_gateway import Principal
from app.infrastructure.repositories import (
    AuditRepository,
    ClientRepository,
    ClientUserRepository,
    CompetencyRepository,
    PreferenceRepository,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AuditService:
    def __init__(self, session: Session) -> None:
        self.repository = AuditRepository(session)

    def record(
        self,
        event_type: AuditEventType,
        actor: Principal,
        context: RequestContext,
        *,
        client_id: str | None = None,
        competency_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.repository.add(
            ClientAuditEvent(
                event_type=event_type.value,
                user_id=actor.id,
                client_id=client_id,
                competency_id=competency_id,
                metadata_json=metadata or {},
                ip_address=context.ip_address,
                user_agent=context.user_agent,
            )
        )


class ClientAccessService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.bindings = ClientUserRepository(session)

    def require(
        self,
        actor: Principal,
        client_id: str,
        context: RequestContext,
        *,
        roles: set[str] | None = None,
        responsibilities: set[str] | None = None,
    ) -> ClientUser | None:
        if actor.is_admin:
            return None
        binding = self.bindings.get(client_id, actor.id)
        permitted = binding is not None and binding.status == LinkStatus.ACTIVE.value
        if roles and permitted:
            permitted = binding.client_role in roles
        if responsibilities and permitted:
            permitted = binding.responsibility_area in responsibilities
        if not permitted:
            AuditService(self.session).record(
                AuditEventType.CLIENT_ACCESS_DENIED,
                actor,
                context,
                client_id=client_id,
            )
            self.session.commit()
            raise ClientAccessDeniedError()
        return binding


class ClientService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.clients = ClientRepository(session)

    def get(self, client_id: str) -> Client:
        client = self.clients.get(client_id)
        if client is None:
            raise NotFoundError("Client")
        return client

    def create(
        self,
        payload: ClientCreate,
        actor: Principal,
        context: RequestContext,
    ) -> Client:
        normalized = normalize_cnpj(payload.cnpj)
        if self.clients.get_by_cnpj(normalized):
            raise ConflictError(
                "CLIENT_CNPJ_ALREADY_EXISTS",
                "Já existe um cliente cadastrado com este CNPJ.",
            )
        if payload.code and self.clients.get_by_code(payload.code):
            raise ConflictError("CLIENT_CODE_ALREADY_EXISTS", "Client code already exists")
        client = Client(
            code=payload.code,
            name=payload.name,
            trade_name=payload.trade_name,
            cnpj=format_cnpj(normalized),
            cnpj_normalized=normalized,
            status=ClientStatus.ACTIVE.value,
            tax_regime=payload.tax_regime.value if payload.tax_regime else None,
            state_registration=payload.state_registration,
            municipal_registration=payload.municipal_registration,
            city=payload.city,
            state=payload.state,
            default_folder_path=payload.default_folder_path,
            competence_folder_pattern=(
                payload.competence_folder_pattern
                or self.settings.default_competence_folder_pattern
            ),
            notes=payload.notes,
            created_by_user_id=actor.id,
        )
        try:
            self.clients.add(client)
            AuditService(self.session).record(
                AuditEventType.CLIENT_CREATED, actor, context, client_id=client.id
            )
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("CLIENT_ALREADY_EXISTS", "Client already exists") from exc
        return client

    def update(
        self,
        client_id: str,
        payload: ClientUpdate,
        actor: Principal,
        context: RequestContext,
    ) -> Client:
        client = self.get(client_id)
        if client.status == ClientStatus.ARCHIVED.value:
            raise BusinessRuleError("CLIENT_ARCHIVED", "Archived client cannot be updated")
        changes = payload.model_dump(exclude_unset=True)
        if "cnpj" in changes and changes["cnpj"] is not None:
            normalized = normalize_cnpj(changes.pop("cnpj"))
            existing = self.clients.get_by_cnpj(normalized)
            if existing and existing.id != client.id:
                raise ConflictError(
                    "CLIENT_CNPJ_ALREADY_EXISTS",
                    "Já existe um cliente cadastrado com este CNPJ.",
                )
            client.cnpj = format_cnpj(normalized)
            client.cnpj_normalized = normalized
        if "code" in changes and changes["code"]:
            existing_code = self.clients.get_by_code(changes["code"])
            if existing_code and existing_code.id != client.id:
                raise ConflictError("CLIENT_CODE_ALREADY_EXISTS", "Client code already exists")
        for field, value in changes.items():
            if hasattr(value, "value"):
                value = value.value
            setattr(client, field, value)
        AuditService(self.session).record(
            AuditEventType.CLIENT_UPDATED,
            actor,
            context,
            client_id=client.id,
            metadata={"fields": sorted(payload.model_fields_set)},
        )
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("CLIENT_ALREADY_EXISTS", "Client already exists") from exc
        return client

    def change_status(
        self,
        client_id: str,
        status: ClientStatus,
        actor: Principal,
        context: RequestContext,
    ) -> Client:
        client = self.get(client_id)
        now = utc_now()
        event = AuditEventType.CLIENT_RESTORED
        if status == ClientStatus.INACTIVE:
            client.status = status.value
            client.disabled_at = now
            event = AuditEventType.CLIENT_DISABLED
        elif status == ClientStatus.ARCHIVED:
            client.status = status.value
            client.archived_at = now
            event = AuditEventType.CLIENT_ARCHIVED
        else:
            client.status = status.value
            client.disabled_at = None
            client.archived_at = None
        AuditService(self.session).record(event, actor, context, client_id=client.id)
        self.session.commit()
        return client

    def update_folder(
        self,
        client_id: str,
        payload: FolderUpdate,
        actor: Principal,
        context: RequestContext,
    ) -> Client:
        client = self.get(client_id)
        if client.status == ClientStatus.ARCHIVED.value:
            raise BusinessRuleError("CLIENT_ARCHIVED", "Archived client cannot be updated")
        for field in payload.model_fields_set:
            value = getattr(payload, field)
            if field == "competence_folder_pattern" and value is None:
                value = self.settings.default_competence_folder_pattern
            setattr(client, field, value)
        AuditService(self.session).record(
            AuditEventType.CLIENT_FOLDER_UPDATED,
            actor,
            context,
            client_id=client.id,
            metadata={"fields": sorted(payload.model_fields_set)},
        )
        self.session.commit()
        return client

    def preview_folder(
        self,
        client_id: str,
        year: int,
        month: int,
        actor: Principal,
        context: RequestContext,
    ) -> tuple[Client, str]:
        client = self.get(client_id)
        path = resolve_competence_path(
            client.default_folder_path or "",
            client.competence_folder_pattern,
            year,
            month,
        )
        AuditService(self.session).record(
            AuditEventType.CLIENT_FOLDER_PREVIEWED,
            actor,
            context,
            client_id=client.id,
            metadata={"period": f"{year:04d}-{month:02d}"},
        )
        self.session.commit()
        return client, path


class CompetencyService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.clients = ClientService(session, settings)
        self.competencies = CompetencyRepository(session)

    def get(self, client_id: str, competency_id: str) -> ClientCompetency:
        competency = self.competencies.get(client_id, competency_id)
        if competency is None:
            raise NotFoundError("Competency")
        return competency

    def create(
        self,
        client_id: str,
        payload: CompetencyCreate,
        actor: Principal,
        context: RequestContext,
    ) -> ClientCompetency:
        client = self.clients.get(client_id)
        if client.status != ClientStatus.ACTIVE.value:
            raise BusinessRuleError("CLIENT_NOT_ACTIVE", "Client must be active")
        period = f"{payload.year:04d}-{payload.month:02d}"
        if self.competencies.get_by_period(client_id, period):
            raise ConflictError(
                "CLIENT_COMPETENCY_ALREADY_EXISTS",
                "Competency already exists for this client and period",
            )
        folder_path = None
        resolved_at = None
        if client.default_folder_path:
            folder_path = resolve_competence_path(
                client.default_folder_path,
                client.competence_folder_pattern,
                payload.year,
                payload.month,
            )
            resolved_at = utc_now()
        competency = ClientCompetency(
            client_id=client.id,
            period=period,
            year=payload.year,
            month=payload.month,
            status=payload.status.value,
            folder_path=folder_path,
            folder_resolved_at=resolved_at,
            created_by_user_id=actor.id,
        )
        try:
            self.competencies.add(competency)
            AuditService(self.session).record(
                AuditEventType.CLIENT_COMPETENCY_CREATED,
                actor,
                context,
                client_id=client.id,
                competency_id=competency.id,
                metadata={"period": period},
            )
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError(
                "CLIENT_COMPETENCY_ALREADY_EXISTS",
                "Competency already exists for this client and period",
            ) from exc
        return competency

    def ensure_current(
        self,
        client_id: str,
        year: int | None,
        month: int | None,
        actor: Principal,
        context: RequestContext,
    ) -> tuple[ClientCompetency, bool]:
        today = date.today()
        target_year = year or today.year
        target_month = month or today.month
        period = f"{target_year:04d}-{target_month:02d}"
        existing = self.competencies.get_by_period(client_id, period)
        if existing:
            return existing, False
        try:
            created = self.create(
                client_id,
                CompetencyCreate(year=target_year, month=target_month),
                actor,
                context,
            )
            return created, True
        except ConflictError:
            existing = self.competencies.get_by_period(client_id, period)
            if existing is None:
                raise
            return existing, False

    def update(
        self,
        client_id: str,
        competency_id: str,
        payload: CompetencyUpdate,
        actor: Principal,
        context: RequestContext,
    ) -> ClientCompetency:
        competency = self.get(client_id, competency_id)
        if competency.status in {CompetencyStatus.CLOSED.value, CompetencyStatus.ARCHIVED.value}:
            raise BusinessRuleError("COMPETENCY_LOCKED", "Closed or archived competency cannot be updated")
        if "folder_path" in payload.model_fields_set:
            competency.folder_path = payload.folder_path
            competency.folder_resolved_at = utc_now() if payload.folder_path else None
        AuditService(self.session).record(
            AuditEventType.CLIENT_COMPETENCY_UPDATED,
            actor,
            context,
            client_id=client_id,
            competency_id=competency.id,
        )
        self.session.commit()
        return competency

    def change_status(
        self,
        client_id: str,
        competency_id: str,
        status: CompetencyStatus,
        actor: Principal,
        context: RequestContext,
    ) -> ClientCompetency:
        competency = self.get(client_id, competency_id)
        if competency.status == CompetencyStatus.ARCHIVED.value:
            raise BusinessRuleError("COMPETENCY_ARCHIVED", "Archived competency cannot be changed")
        if competency.status == CompetencyStatus.CLOSED.value and status != CompetencyStatus.ARCHIVED:
            raise BusinessRuleError("COMPETENCY_CLOSED", "Closed competency cannot be reopened")
        competency.status = status.value
        event = AuditEventType.CLIENT_COMPETENCY_STATUS_CHANGED
        if status == CompetencyStatus.ARCHIVED:
            competency.archived_at = utc_now()
            event = AuditEventType.CLIENT_COMPETENCY_ARCHIVED
        AuditService(self.session).record(
            event,
            actor,
            context,
            client_id=client_id,
            competency_id=competency.id,
            metadata={"status": status.value},
        )
        self.session.commit()
        return competency

    def close(
        self,
        client_id: str,
        competency_id: str,
        actor: Principal,
        context: RequestContext,
    ) -> ClientCompetency:
        competency = self.get(client_id, competency_id)
        if competency.status == CompetencyStatus.ARCHIVED.value:
            raise BusinessRuleError("COMPETENCY_ARCHIVED", "Archived competency cannot be closed")
        competency.status = CompetencyStatus.CLOSED.value
        competency.closed_at = utc_now()
        competency.closed_by_user_id = actor.id
        AuditService(self.session).record(
            AuditEventType.CLIENT_COMPETENCY_CLOSED,
            actor,
            context,
            client_id=client_id,
            competency_id=competency.id,
        )
        self.session.commit()
        return competency


class ClientUserService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.clients = ClientService(session, settings)
        self.bindings = ClientUserRepository(session)

    def get(self, client_id: str, user_id: str) -> ClientUser:
        binding = self.bindings.get(client_id, user_id)
        if binding is None:
            raise NotFoundError("Client user")
        return binding

    def create(
        self,
        client_id: str,
        payload: ClientUserCreate,
        actor: Principal,
        context: RequestContext,
    ) -> ClientUser:
        client = self.clients.get(client_id)
        if client.status != ClientStatus.ACTIVE.value:
            raise BusinessRuleError("CLIENT_NOT_ACTIVE", "Client must be active")
        if self.bindings.get(client_id, payload.user_id):
            raise ConflictError("CLIENT_USER_ALREADY_EXISTS", "User is already linked to this client")
        binding = ClientUser(
            client_id=client_id,
            user_id=payload.user_id,
            client_role=payload.client_role.value,
            status=LinkStatus.ACTIVE.value,
            is_primary_responsible=payload.is_primary_responsible,
            responsibility_area=payload.responsibility_area.value,
        )
        try:
            self.bindings.add(binding)
            AuditService(self.session).record(
                AuditEventType.CLIENT_USER_LINKED,
                actor,
                context,
                client_id=client_id,
                metadata={"linkedUserId": payload.user_id},
            )
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("CLIENT_USER_ALREADY_EXISTS", "User is already linked to this client") from exc
        return binding

    def update(
        self,
        client_id: str,
        user_id: str,
        payload: ClientUserUpdate,
        actor: Principal,
        context: RequestContext,
    ) -> ClientUser:
        binding = self.get(client_id, user_id)
        for field in payload.model_fields_set:
            value = getattr(payload, field)
            if hasattr(value, "value"):
                value = value.value
            setattr(binding, field, value)
        if payload.status == LinkStatus.INACTIVE:
            binding.disabled_at = utc_now()
        elif payload.status == LinkStatus.ACTIVE:
            binding.disabled_at = None
        AuditService(self.session).record(
            AuditEventType.CLIENT_USER_UPDATED,
            actor,
            context,
            client_id=client_id,
            metadata={"linkedUserId": user_id, "fields": sorted(payload.model_fields_set)},
        )
        self.session.commit()
        return binding

    def disable(
        self,
        client_id: str,
        user_id: str,
        actor: Principal,
        context: RequestContext,
    ) -> ClientUser:
        binding = self.get(client_id, user_id)
        binding.status = LinkStatus.INACTIVE.value
        binding.disabled_at = utc_now()
        AuditService(self.session).record(
            AuditEventType.CLIENT_USER_UNLINKED,
            actor,
            context,
            client_id=client_id,
            metadata={"linkedUserId": user_id},
        )
        self.session.commit()
        return binding


class PreferenceService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.preferences = PreferenceRepository(session)
        self.clients = ClientService(session, settings)
        self.competencies = CompetencyRepository(session)

    def get(self, user_id: str) -> UserClientPreference | None:
        return self.preferences.get(user_id)

    def update(
        self,
        payload: PreferenceUpdate,
        actor: Principal,
        context: RequestContext,
    ) -> UserClientPreference:
        if payload.default_client_id:
            client = self.clients.get(payload.default_client_id)
            if client.status != ClientStatus.ACTIVE.value:
                raise BusinessRuleError("CLIENT_NOT_ACTIVE", "Default client must be active")
            ClientAccessService(self.session).require(actor, client.id, context)
            if payload.default_competence_period and not self.competencies.get_by_period(
                client.id, payload.default_competence_period
            ):
                raise BusinessRuleError("COMPETENCY_NOT_FOUND", "Default competency does not exist")
        preference = self.preferences.get(actor.id)
        if preference is None:
            preference = self.preferences.add(UserClientPreference(user_id=actor.id))
        for field in payload.model_fields_set:
            setattr(preference, field, getattr(payload, field))
        self.session.commit()
        return preference
