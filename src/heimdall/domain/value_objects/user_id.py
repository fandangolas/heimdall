"""User ID value object - functional approach."""

import uuid
from typing import NamedTuple


class UserIdValue(NamedTuple):
    """User identifier value object."""

    value: str

    def __str__(self) -> str:
        """String representation."""
        return self.value


def UserId(user_id_string: str) -> UserIdValue:
    """Create and validate a user ID value object."""
    if not user_id_string:
        raise ValueError("User ID cannot be empty")

    # Validate UUID format
    try:
        uuid.UUID(user_id_string)
    except ValueError as e:
        raise ValueError(f"Invalid user ID format: {user_id_string}") from e

    return UserIdValue(value=user_id_string)


def generate_user_id() -> UserIdValue:
    """Generate a new user ID."""
    return UserId(str(uuid.uuid4()))


# For backwards compatibility, add generate method
UserIdValue.generate = staticmethod(generate_user_id)
