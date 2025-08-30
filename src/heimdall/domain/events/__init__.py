"""Domain events - Capture important state changes."""

from .base import DomainEvent, DomainEventValue
from .user_events import (
    UserActivated,
    UserCreated,
    UserDeactivated,
    UserLoggedIn,
    UserLoggedOut,
    UserPasswordChanged,
    UserPermissionGranted,
    UserPermissionRevoked,
)

__all__ = [
    "DomainEvent",
    "DomainEventValue",
    "UserActivated",
    "UserCreated",
    "UserDeactivated",
    "UserLoggedIn",
    "UserLoggedOut",
    "UserPasswordChanged",
    "UserPermissionGranted",
    "UserPermissionRevoked",
]
