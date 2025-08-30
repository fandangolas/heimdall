"""Base domain event."""

import uuid
from datetime import UTC, datetime
from typing import Any, NamedTuple


class DomainEventValue(NamedTuple):
    """Base structure for all domain events."""

    event_id: str
    event_type: str
    occurred_at: datetime
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "data": self.data,
        }


def DomainEvent(
    event_type: str,
    data: dict[str, Any],
    event_id: str | None = None,
    occurred_at: datetime | None = None,
) -> DomainEventValue:
    """Create a domain event."""
    if event_id is None:
        event_id = str(uuid.uuid4())
    if occurred_at is None:
        occurred_at = datetime.now(UTC)

    return DomainEventValue(
        event_id=event_id,
        event_type=event_type,
        occurred_at=occurred_at,
        data=data,
    )
