"""Token validation DTOs."""

from dataclasses import dataclass


@dataclass
class ValidateTokenRequest:
    """Token validation request data."""

    token: str


@dataclass
class ValidateTokenResponse:
    """Token validation response data."""

    is_valid: bool
    user_id: str | None = None
    email: str | None = None
    permissions: list[str] | None = None
    error: str | None = None
