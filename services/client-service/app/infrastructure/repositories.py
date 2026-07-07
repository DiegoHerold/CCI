from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.domain.enums import ClientStatus, LinkStatus
from app.infrastructure.database.models import (
    Client,
    ClientAuditEvent,
    ClientCompetency,
    ClientUser,
    UserClientPreference,
)


class ClientRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, client_id: str) -> Client | None:
        return self.session.get(Client, client_id)

    def get_by_cnpj(self, cnpj_normalized: str) -> Client | None:
        return self.session.scalar(
            select(Client).where(Client.cnpj_normalized == cnpj_normalized)
        )

    def get_by_code(self, code: str) -> Client | None:
        return self.session.scalar(select(Client).where(Client.code == code))

    def add(self, client: Client) -> Client:
        self.session.add(client)
        self.session.flush()
        return client

    def list_accessible(
        self,
        user_id: str,
        is_admin: bool,
        *,
        status: str | None = None,
        search: str | None = None,
        cnpj: str | None = None,
        city: str | None = None,
        state: str | None = None,
        tax_regime: str | None = None,
        responsibility_area: str | None = None,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "name",
        sort_direction: str = "asc",
    ) -> tuple[list[Client], int]:
        statement = select(Client)
        joined = False
        if not is_admin:
            statement = statement.join(
                ClientUser,
                (ClientUser.client_id == Client.id)
                & (ClientUser.user_id == user_id)
                & (ClientUser.status == LinkStatus.ACTIVE.value),
            )
            joined = True
        if responsibility_area:
            if not joined:
                statement = statement.join(ClientUser, ClientUser.client_id == Client.id)
            statement = statement.where(
                ClientUser.responsibility_area == responsibility_area,
                ClientUser.status == LinkStatus.ACTIVE.value,
            )
        if status:
            statement = statement.where(Client.status == status)
        else:
            statement = statement.where(Client.status != ClientStatus.ARCHIVED.value)
        if search:
            term = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    Client.name.ilike(term),
                    Client.trade_name.ilike(term),
                    Client.code.ilike(term),
                    Client.cnpj_normalized.ilike(term),
                )
            )
        if cnpj:
            statement = statement.where(Client.cnpj_normalized == cnpj)
        if city:
            statement = statement.where(Client.city.ilike(city.strip()))
        if state:
            statement = statement.where(Client.state == state.upper())
        if tax_regime:
            statement = statement.where(Client.tax_regime == tax_regime)
        statement = statement.distinct()
        total = self.session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        ) or 0
        columns = {
            "name": Client.name,
            "tradeName": Client.trade_name,
            "code": Client.code,
            "cnpj": Client.cnpj_normalized,
            "status": Client.status,
            "createdAt": Client.created_at,
            "updatedAt": Client.updated_at,
        }
        order = columns[sort_by]
        statement = statement.order_by(
            order.desc() if sort_direction == "desc" else order.asc(), Client.id.asc()
        )
        statement = statement.offset((page - 1) * limit).limit(limit)
        return list(self.session.scalars(statement).all()), int(total)


class ClientUserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, client_id: str, user_id: str) -> ClientUser | None:
        return self.session.scalar(
            select(ClientUser).where(
                ClientUser.client_id == client_id, ClientUser.user_id == user_id
            )
        )

    def add(self, binding: ClientUser) -> ClientUser:
        self.session.add(binding)
        self.session.flush()
        return binding

    def list(
        self,
        client_id: str,
        *,
        status: str | None,
        client_role: str | None,
        responsibility_area: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[ClientUser], int]:
        statement = select(ClientUser).where(ClientUser.client_id == client_id)
        if status:
            statement = statement.where(ClientUser.status == status)
        if client_role:
            statement = statement.where(ClientUser.client_role == client_role)
        if responsibility_area:
            statement = statement.where(ClientUser.responsibility_area == responsibility_area)
        total = self.session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        ) or 0
        statement = statement.order_by(ClientUser.created_at).offset((page - 1) * limit).limit(limit)
        return list(self.session.scalars(statement).all()), int(total)


class CompetencyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, client_id: str, competency_id: str) -> ClientCompetency | None:
        return self.session.scalar(
            select(ClientCompetency).where(
                ClientCompetency.client_id == client_id,
                ClientCompetency.id == competency_id,
            )
        )

    def get_by_period(self, client_id: str, period: str) -> ClientCompetency | None:
        return self.session.scalar(
            select(ClientCompetency).where(
                ClientCompetency.client_id == client_id,
                ClientCompetency.period == period,
            )
        )

    def add(self, competency: ClientCompetency) -> ClientCompetency:
        self.session.add(competency)
        self.session.flush()
        return competency

    def list(
        self,
        client_id: str,
        *,
        status: str | None,
        year: int | None,
        from_period: str | None,
        to_period: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[ClientCompetency], int]:
        statement = select(ClientCompetency).where(ClientCompetency.client_id == client_id)
        if status:
            statement = statement.where(ClientCompetency.status == status)
        if year:
            statement = statement.where(ClientCompetency.year == year)
        if from_period:
            statement = statement.where(ClientCompetency.period >= from_period)
        if to_period:
            statement = statement.where(ClientCompetency.period <= to_period)
        total = self.session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        ) or 0
        statement = statement.order_by(ClientCompetency.period.desc()).offset((page - 1) * limit).limit(limit)
        return list(self.session.scalars(statement).all()), int(total)


class PreferenceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, user_id: str) -> UserClientPreference | None:
        return self.session.scalar(
            select(UserClientPreference).where(UserClientPreference.user_id == user_id)
        )

    def add(self, preference: UserClientPreference) -> UserClientPreference:
        self.session.add(preference)
        self.session.flush()
        return preference


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, event: ClientAuditEvent) -> None:
        self.session.add(event)
