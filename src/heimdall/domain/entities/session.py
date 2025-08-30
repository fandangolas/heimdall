"""Session entity."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

# No typing imports needed - using built-in types
from ..value_objects import Email, SessionId, TokenClaims, UserId


@dataclass
class Session:
    """Session entity - represents an active user session."""

    id: SessionId
    user_id: UserId
    email: Email
    permissions: list[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = field(
        default_factory=lambda: datetime.now(UTC) + timedelta(hours=24)
    )
    is_active: bool = True

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now(UTC) > self.expires_at

    def is_valid(self) -> bool:
        """Check if session is valid: active and not expired."""
        return self.is_active and not self.is_expired()

    def invalidate(self) -> None:
        """Invalidate the session."""
        self.is_active = False

    def to_token_claims(self) -> TokenClaims:
        """Convert session to token claims."""
        return TokenClaims(
            user_id=str(self.user_id),
            session_id=str(self.id),
            email=str(self.email),
            permissions=self.permissions.copy(),
        )

    @classmethod
    def create_for_user(
        cls, user_id: UserId, email: Email, permissions: list[str]
    ) -> "Session":
        """Create a new session for a user."""
        return cls(
            id=SessionId.generate(),
            user_id=user_id,
            email=email,
            permissions=permissions.copy(),
        )
