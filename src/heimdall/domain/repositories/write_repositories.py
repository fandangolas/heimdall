"""Write-optimized repository interfaces for CQRS commands."""

from abc import ABC, abstractmethod

from ..entities import Session, User
from ..value_objects import Email, SessionId, UserId


class WriteUserRepository(ABC):
    """Write-optimized user repository for commands (0.1% of traffic).

    This interface handles user state changes and can afford stronger
    consistency guarantees since it's used infrequently.
    """

    @abstractmethod
    async def find_by_email(self, email: Email) -> User | None:
        """Find user by email for authentication."""

    @abstractmethod
    async def exists_by_email(self, email: Email) -> bool:
        """Check if user exists by email."""

    @abstractmethod
    async def save(self, user: User) -> None:
        """Save user (create or update)."""

    @abstractmethod
    async def find_by_id(self, user_id: UserId) -> User | None:
        """Find user by ID."""


class WriteSessionRepository(ABC):
    """Write-optimized session repository for commands.

    Handles session creation and state changes. Can use stronger
    consistency since it's only used during login/logout.
    """

    @abstractmethod
    async def find_by_id(self, session_id: SessionId) -> Session | None:
        """Find session by ID for commands."""

    @abstractmethod
    async def save(self, session: Session) -> None:
        """Save session (create or update)."""
