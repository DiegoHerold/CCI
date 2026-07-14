from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class DomainEvent:
    event_type: str
    payload: dict[str, Any]
    correlation_id: str
    client_id: str | None = None
    competence_id: str | None = None
    document_id: str | None = None
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def as_envelope(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "version": 1,
            "occurred_at": self.occurred_at.isoformat(),
            "correlation_id": self.correlation_id,
            "producer": "extraction-service",
            "client_id": self.client_id,
            "competence_id": self.competence_id,
            "document_id": self.document_id,
            "payload": self.payload,
        }


class EventPublisher:
    def publish(self, event: DomainEvent) -> None:
        return None


class NoOpEventPublisher(EventPublisher):
    pass
