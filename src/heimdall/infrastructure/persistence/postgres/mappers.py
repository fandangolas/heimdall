"""Pure functions for mapping between database rows and domain entities.

These are functional components that handle the transformation between
database schema and domain objects without side effects.
"""

from typing import Any

from heimdall.domain.entities import Session, User
from heimdall.domain.value_objects import Email, SessionId, UserId
from heimdall.domain.value_objects.password import PasswordHashValue


def row_to_user(row: dict[str, Any]) -> User:
    """Pure function to convert database row to User entity.

    Args:
        row: Database row with user data

    Returns:
        User domain entity
    """
    # Map database schema to domain entity
    is_active = row["status"] == "active"
    return User(
        id=UserId(str(row["id"])),
        email=Email(row["email"]),
        password_hash=PasswordHashValue(row["password_hash"]),
        is_active=is_active,
        is_verified=row["is_verified"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_login_at=row["last_login_at"],
    )


def row_to_session(row: dict[str, Any]) -> Session:
    """Pure function to convert database row to Session entity.

    Args:
        row: Database row with session data

    Returns:
        Session domain entity
    """
    # Map database schema to domain entity
    is_active = row["status"] == "active"

    # For now, we'll use empty permissions list - in real implementation,
    # you'd probably join with user_permissions or role_permissions tables
    return Session(
        id=SessionId(str(row["id"])),
        user_id=UserId(str(row["user_id"])),
        email=Email(row["email"]),
        permissions=[],  # TODO: Load from user_permissions/role_permissions
        created_at=row["created_at"],
        expires_at=row["expires_at"],
        is_active=is_active,
    )


def user_to_db_params(user: User) -> dict[str, Any]:
    """Pure function to convert User entity to database parameters.

    Args:
        user: User domain entity

    Returns:
        Dictionary with database parameters
    """
    return {
        "id": str(user.id),
        "email": str(user.email),
        "password_hash": user.password_hash.value,
        "status": "active" if user.is_active else "inactive",
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "last_login_at": user.last_login_at,
    }


def session_to_db_params(session: Session) -> dict[str, Any]:
    """Pure function to convert Session entity to database parameters.

    Args:
        session: Session domain entity

    Returns:
        Dictionary with database parameters
    """
    # Generate a simple token hash for the session
    # (in real implementation, this would be the JWT hash)
    token_hash = f"hash_{session.id}_{session.user_id}"

    return {
        "id": str(session.id),
        "user_id": str(session.user_id),
        "status": "active" if session.is_active else "invalidated",
        "created_at": session.created_at,
        "expires_at": session.expires_at,
        "token_hash": token_hash,
    }
