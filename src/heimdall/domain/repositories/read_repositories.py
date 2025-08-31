"""Read-optimized repository interfaces for CQRS queries."""

from abc import ABC, abstractmethod

from ..entities import Session
from ..value_objects import SessionId


class ReadSessionRepository(ABC):
    """Read-optimized session repository for queries (99% of traffic).

    This interface is optimized for fast token validation lookups.
    Could be backed by Redis cache, read replicas, or denormalized views.
    """

    @abstractmethod
    async def find_by_id(self, session_id: SessionId) -> Session | None:
        """Fast session lookup - optimized for token validation.

        This is the critical path for 99% of operations.
        Implementation should prioritize speed over consistency.
        """
