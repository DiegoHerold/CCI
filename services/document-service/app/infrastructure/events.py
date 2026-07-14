from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class DomainEvent:
    event_id: str
    event_type: str
    occurred_at: datetime
    correlation_id: str
    payload: dict[str, Any]

    @classmethod
    def create(
        cls, event_type: str, correlation_id: str, payload: dict[str, Any]
    ) -> "DomainEvent":
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            occurred_at=datetime.now(timezone.utc),
            correlation_id=correlation_id,
            payload=payload,
        )


class EventPublisher:
    def publish(self, event: DomainEvent) -> None:
        raise NotImplementedError


class NoOpEventPublisher(EventPublisher):
    def publish(self, event: DomainEvent) -> None:
        return None
