"""Token validation DTOs."""

from typing import NamedTuple


class ValidateTokenRequestValue(NamedTuple):
    """Token validation request data structure."""

    token: str


class ValidateTokenResponseValue(NamedTuple):
    """Token validation response data structure."""

    is_valid: bool
    user_id: str | None
    email: str | None
    permissions: tuple[str, ...] | None
    error: str | None


def ValidateTokenRequest(token: str) -> ValidateTokenRequestValue:
    """Create token validation request."""
    return ValidateTokenRequestValue(token=token)


def ValidateTokenResponse(
    is_valid: bool,
    user_id: str | None = None,
    email: str | None = None,
    permissions: list[str] | None = None,
    error: str | None = None,
) -> ValidateTokenResponseValue:
    """Create token validation response."""
    # Convert list to tuple for immutability
    perms_tuple = tuple(permissions) if permissions else None

    return ValidateTokenResponseValue(
        is_valid=is_valid,
        user_id=user_id,
        email=email,
        permissions=perms_tuple,
        error=error,
    )
