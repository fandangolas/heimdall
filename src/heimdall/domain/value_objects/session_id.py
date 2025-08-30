"""Session ID value object - functional approach."""

import uuid
from typing import NamedTuple


class SessionIdValue(NamedTuple):
    """Session identifier value object."""

    value: str

    def __str__(self) -> str:
        """String representation."""
        return self.value


def SessionId(session_id_string: str) -> SessionIdValue:
    """Create and validate a session ID value object."""
    if not session_id_string:
        raise ValueError("Session ID cannot be empty")

    # Validate UUID format
    try:
        uuid.UUID(session_id_string)
    except ValueError as e:
        raise ValueError(f"Invalid session ID format: {session_id_string}") from e

    return SessionIdValue(value=session_id_string)


def generate_session_id() -> SessionIdValue:
    """Generate a new session ID."""
    return SessionId(str(uuid.uuid4()))


# For backwards compatibility, add generate method
SessionIdValue.generate = staticmethod(generate_session_id)
