from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True)
class DomainEvent:
    event_type: str
    payload: dict
    correlation_id: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    producer: str = "template-service"
    version: int = 1

    def envelope(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "version": self.version,
            "occurred_at": self.occurred_at,
            "correlation_id": self.correlation_id,
            "producer": self.producer,
            "payload": self.payload,
        }


class EventPublisher:
    def publish(self, event: DomainEvent) -> None:
        raise NotImplementedError


class NoOpEventPublisher(EventPublisher):
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self.events.append(event)
