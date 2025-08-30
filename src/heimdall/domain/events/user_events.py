"""User-related domain events."""

from dataclasses import dataclass
from typing import List, Optional

from ..value_objects import Email, UserId, SessionId
from .base import DomainEvent


@dataclass
class UserCreated(DomainEvent):
    """Event raised when a new user is created."""
    
    user_id: UserId
    email: Email


@dataclass
class UserLoggedIn(DomainEvent):
    """Event raised when a user logs in."""
    
    user_id: UserId
    session_id: SessionId
    email: Email


@dataclass
class UserLoggedOut(DomainEvent):
    """Event raised when a user logs out."""
    
    user_id: UserId
    session_id: SessionId


@dataclass
class UserPasswordChanged(DomainEvent):
    """Event raised when a user changes their password."""
    
    user_id: UserId


@dataclass
class UserPermissionGranted(DomainEvent):
    """Event raised when a permission is granted to a user."""
    
    user_id: UserId
    permission: str


@dataclass
class UserPermissionRevoked(DomainEvent):
    """Event raised when a permission is revoked from a user."""
    
    user_id: UserId
    permission: str


@dataclass
class UserDeactivated(DomainEvent):
    """Event raised when a user account is deactivated."""
    
    user_id: UserId
    reason: Optional[str] = None


@dataclass
class UserActivated(DomainEvent):
    """Event raised when a user account is activated."""
    
    user_id: UserId