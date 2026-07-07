from typing import Any

from sqlalchemy.orm import Session

from app.application.context import RequestContext
from app.domain.audit import IdentityAuditEventType
from app.infrastructure.database.models import IdentityAuditEvent
from app.infrastructure.repositories import AuditRepository


class IdentityAuditService:
    def __init__(self, session: Session) -> None:
        self.repository = AuditRepository(session)

    def record(
        self,
        event_type: IdentityAuditEventType,
        context: RequestContext,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.repository.add(
            IdentityAuditEvent(
                user_id=user_id,
                event_type=event_type.value,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                metadata_json=metadata or {},
            )
        )
