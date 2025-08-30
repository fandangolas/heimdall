"""Base domain event."""

import uuid
from datetime import UTC, datetime
from typing import Any


class DomainEvent:
    """Base class for all domain events."""

    def __init__(self, **kwargs):
        self.event_id = kwargs.get("event_id", str(uuid.uuid4()))
        self.occurred_at = kwargs.get("occurred_at", datetime.now(UTC))

    @property
    def event_type(self) -> str:
        """Get the event type name."""
        return self.__class__.__name__

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "data": self._get_event_data(),
        }

    def _get_event_data(self) -> dict[str, Any]:
        """Get event-specific data. Override in subclasses."""
        data = {}
        for key, value in self.__dict__.items():
            if key not in ["event_id", "occurred_at"]:
                if hasattr(value, "__dict__"):
                    data[key] = str(value)
                else:
                    data[key] = value
        return data
