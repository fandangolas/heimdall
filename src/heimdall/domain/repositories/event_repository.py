"""Event repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime

from ..events import DomainEvent


class EventRepository(ABC):
    """Abstract interface for event persistence."""

    @abstractmethod
    async def save(self, event: DomainEvent) -> None:
        """Save a domain event."""

    @abstractmethod
    async def find_by_aggregate_id(self, aggregate_id: str) -> list[DomainEvent]:
        """Find all events for an aggregate."""

    @abstractmethod
    async def find_by_time_range(
        self, start_time: datetime, end_time: datetime
    ) -> list[DomainEvent]:
        """Find events within a time range."""
