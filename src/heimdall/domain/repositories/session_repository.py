"""Session repository interface."""

from abc import ABC, abstractmethod
from typing import Optional

from ..entities import Session
from ..value_objects import SessionId, UserId


class SessionRepository(ABC):
    """Abstract interface for session persistence."""
    
    @abstractmethod
    async def find_by_id(self, session_id: SessionId) -> Optional[Session]:
        """Find a session by ID."""
        pass
    
    @abstractmethod
    async def find_active_by_user(self, user_id: UserId) -> list[Session]:
        """Find all active sessions for a user."""
        pass
    
    @abstractmethod
    async def save(self, session: Session) -> None:
        """Save a session (create or update)."""
        pass
    
    @abstractmethod
    async def delete(self, session_id: SessionId) -> None:
        """Delete a session."""
        pass
    
    @abstractmethod
    async def delete_all_by_user(self, user_id: UserId) -> None:
        """Delete all sessions for a user."""
        pass