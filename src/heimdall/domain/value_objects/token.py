"""Token value objects."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class TokenClaims:
    """JWT token claims."""

    user_id: str
    session_id: str
    email: str
    permissions: list[str] = field(default_factory=list)
    issued_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        """Set default expiration if not provided."""
        if self.expires_at is None:
            # Default to 15 minutes from issued_at
            expires = self.issued_at + timedelta(minutes=15)
            object.__setattr__(self, "expires_at", expires)

    def is_expired(self) -> bool:
        """Check if token claims are expired."""
        return datetime.now(UTC) > self.expires_at

    def to_dict(self) -> dict:
        """Convert to dictionary for JWT encoding."""
        return {
            "sub": self.user_id,
            "sid": self.session_id,
            "email": self.email,
            "permissions": self.permissions,
            "iat": int(self.issued_at.timestamp()),
            "exp": int(self.expires_at.timestamp()),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TokenClaims":
        """Create from JWT decoded dictionary."""
        return cls(
            user_id=data["sub"],
            session_id=data["sid"],
            email=data["email"],
            permissions=data.get("permissions", []),
            issued_at=datetime.fromtimestamp(data["iat"], tz=UTC),
            expires_at=datetime.fromtimestamp(data["exp"], tz=UTC),
        )


@dataclass(frozen=True)
class Token:
    """JWT token value object."""

    value: str
    claims: TokenClaims | None = None

    def __post_init__(self) -> None:
        """Validate token format."""
        if not self.value:
            raise ValueError("Token cannot be empty")

        # Basic JWT format validation (three parts separated by dots)
        parts = self.value.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")

    def __str__(self) -> str:
        """String representation (masked for security)."""
        return f"Token(...{self.value[-10:]})"
