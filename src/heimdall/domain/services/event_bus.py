"""Event bus interface."""

from abc import ABC, abstractmethod

from ..events import DomainEvent


class EventBus(ABC):
    """Abstract interface for event publishing."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event."""
