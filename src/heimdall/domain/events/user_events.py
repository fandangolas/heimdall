"""User-related domain events."""

from ..value_objects import Email, SessionId, UserId
from .base import DomainEvent, DomainEventValue


def UserCreated(user_id: UserId, email: Email) -> DomainEventValue:
    """Create UserCreated event."""
    return DomainEvent(
        event_type="UserCreated",
        data={
            "user_id": str(user_id),
            "email": str(email),
        },
    )


def UserLoggedIn(
    user_id: UserId, session_id: SessionId, email: Email
) -> DomainEventValue:
    """Create UserLoggedIn event."""
    return DomainEvent(
        event_type="UserLoggedIn",
        data={
            "user_id": str(user_id),
            "session_id": str(session_id),
            "email": str(email),
        },
    )


def UserLoggedOut(user_id: UserId, session_id: SessionId) -> DomainEventValue:
    """Create UserLoggedOut event."""
    return DomainEvent(
        event_type="UserLoggedOut",
        data={
            "user_id": str(user_id),
            "session_id": str(session_id),
        },
    )


def UserPasswordChanged(user_id: UserId) -> DomainEventValue:
    """Create UserPasswordChanged event."""
    return DomainEvent(
        event_type="UserPasswordChanged",
        data={
            "user_id": str(user_id),
        },
    )


def UserPermissionGranted(user_id: UserId, permission: str) -> DomainEventValue:
    """Create UserPermissionGranted event."""
    return DomainEvent(
        event_type="UserPermissionGranted",
        data={
            "user_id": str(user_id),
            "permission": permission,
        },
    )


def UserPermissionRevoked(user_id: UserId, permission: str) -> DomainEventValue:
    """Create UserPermissionRevoked event."""
    return DomainEvent(
        event_type="UserPermissionRevoked",
        data={
            "user_id": str(user_id),
            "permission": permission,
        },
    )


def UserDeactivated(user_id: UserId, reason: str | None = None) -> DomainEventValue:
    """Create UserDeactivated event."""
    data = {"user_id": str(user_id)}
    if reason is not None:
        data["reason"] = reason

    return DomainEvent(event_type="UserDeactivated", data=data)


def UserActivated(user_id: UserId) -> DomainEventValue:
    """Create UserActivated event."""
    return DomainEvent(
        event_type="UserActivated",
        data={
            "user_id": str(user_id),
        },
    )
