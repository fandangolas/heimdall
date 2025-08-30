"""Domain events - Capture important state changes."""

from .base import DomainEvent
from .user_events import (
    UserCreated,
    UserLoggedIn,
    UserLoggedOut,
    UserPasswordChanged,
    UserPermissionGranted,
    UserPermissionRevoked,
    UserDeactivated,
    UserActivated,
)

__all__ = [
    "DomainEvent",
    "UserCreated",
    "UserLoggedIn",
    "UserLoggedOut",
    "UserPasswordChanged",
    "UserPermissionGranted",
    "UserPermissionRevoked",
    "UserDeactivated",
    "UserActivated",
]