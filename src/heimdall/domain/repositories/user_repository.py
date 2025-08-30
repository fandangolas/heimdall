"""User repository interface."""

from abc import ABC, abstractmethod
from typing import Optional

from ..entities import User
from ..value_objects import Email, UserId


class UserRepository(ABC):
    """Abstract interface for user persistence."""
    
    @abstractmethod
    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        """Find a user by ID."""
        pass
    
    @abstractmethod
    async def find_by_email(self, email: Email) -> Optional[User]:
        """Find a user by email."""
        pass
    
    @abstractmethod
    async def save(self, user: User) -> None:
        """Save a user (create or update)."""
        pass
    
    @abstractmethod
    async def delete(self, user_id: UserId) -> None:
        """Delete a user."""
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: Email) -> bool:
        """Check if a user exists with the given email."""
        pass