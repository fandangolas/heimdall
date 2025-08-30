"""User-related domain events."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
import uuid

from ..value_objects import Email, UserId, SessionId
from .base import DomainEvent


@dataclass
class UserCreated(DomainEvent):
    """Event raised when a new user is created."""
    
    user_id: UserId
    email: Email
    
    def __post_init__(self):
        super().__init__()


@dataclass
class UserLoggedIn(DomainEvent):
    """Event raised when a user logs in."""
    
    user_id: UserId
    session_id: SessionId
    email: Email
    
    def __post_init__(self):
        super().__init__()


@dataclass
class UserLoggedOut(DomainEvent):
    """Event raised when a user logs out."""
    
    user_id: UserId
    session_id: SessionId
    
    def __post_init__(self):
        super().__init__()


@dataclass
class UserPasswordChanged(DomainEvent):
    """Event raised when a user changes their password."""
    
    user_id: UserId
    
    def __post_init__(self):
        super().__init__()


@dataclass
class UserPermissionGranted(DomainEvent):
    """Event raised when a permission is granted to a user."""
    
    user_id: UserId
    permission: str
    
    def __post_init__(self):
        super().__init__()


@dataclass
class UserPermissionRevoked(DomainEvent):
    """Event raised when a permission is revoked from a user."""
    
    user_id: UserId
    permission: str
    
    def __post_init__(self):
        super().__init__()


@dataclass
class UserDeactivated(DomainEvent):
    """Event raised when a user account is deactivated."""
    
    user_id: UserId
    reason: Optional[str] = None
    
    def __post_init__(self):
        super().__init__()


@dataclass
class UserActivated(DomainEvent):
    """Event raised when a user account is activated."""
    
    user_id: UserId
    
    def __post_init__(self):
        super().__init__()