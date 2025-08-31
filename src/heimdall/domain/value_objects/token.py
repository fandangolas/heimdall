"""Token value objects - functional approach."""

from datetime import UTC, datetime, timedelta
from typing import NamedTuple


class TokenClaimsValue(NamedTuple):
    """JWT token claims."""

    user_id: str
    session_id: str
    email: str
    permissions: tuple[str, ...]
    issued_at: datetime
    expires_at: datetime

    def is_expired(self) -> bool:
        """Check if token claims are expired."""
        return datetime.now(UTC) > self.expires_at

    def to_dict(self) -> dict:
        """Convert to dictionary for JWT encoding."""
        return {
            "sub": self.user_id,
            "sid": self.session_id,
            "email": self.email,
            "permissions": list(self.permissions),
            "iat": int(self.issued_at.timestamp()),
            "exp": int(self.expires_at.timestamp()),
        }


class TokenValue(NamedTuple):
    """JWT token value object."""

    value: str
    claims: TokenClaimsValue | None = None

    def __str__(self) -> str:
        """String representation (masked for security)."""
        return f"Token(...{self.value[-10:]})"


def TokenClaims(
    user_id: str,
    session_id: str,
    email: str,
    permissions: list[str] | None = None,
    expires_at: datetime | None = None,
) -> TokenClaimsValue:
    """Create token claims with defaults."""
    if permissions is None:
        permissions = []

    issued_at = datetime.now(UTC)

    if expires_at is None:
        expires_at = issued_at + timedelta(minutes=15)

    return TokenClaimsValue(
        user_id=user_id,
        session_id=session_id,
        email=email,
        permissions=tuple(permissions),  # Convert to tuple for immutability
        issued_at=issued_at,
        expires_at=expires_at,
    )


def TokenClaimsFromDict(data: dict) -> TokenClaimsValue:
    """Create token claims from JWT decoded dictionary."""
    return TokenClaimsValue(
        user_id=data["sub"],
        session_id=data["sid"],
        email=data["email"],
        permissions=tuple(data.get("permissions", [])),
        issued_at=datetime.fromtimestamp(data["iat"], tz=UTC),
        expires_at=datetime.fromtimestamp(data["exp"], tz=UTC),
    )


def Token(token_string: str, claims: TokenClaimsValue | None = None) -> TokenValue:
    """Create and validate a JWT token value object."""
    if not token_string:
        raise ValueError("Token cannot be empty")

    # Basic JWT format validation (three parts separated by dots)
    parts = token_string.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")

    return TokenValue(value=token_string, claims=claims)


# Add backward compatibility methods
TokenClaimsValue.from_dict = staticmethod(TokenClaimsFromDict)
