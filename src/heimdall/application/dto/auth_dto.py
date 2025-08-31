"""Authentication DTOs."""

from typing import NamedTuple


class LoginRequestValue(NamedTuple):
    """Login request data structure."""

    email: str
    password: str


class LoginResponseValue(NamedTuple):
    """Login response data structure."""

    access_token: str
    token_type: str
    expires_in: int


class RegisterRequestValue(NamedTuple):
    """Registration request data structure."""

    email: str
    password: str


class RegisterResponseValue(NamedTuple):
    """Registration response data structure."""

    user_id: str
    email: str
    message: str


def LoginRequest(email: str, password: str) -> LoginRequestValue:
    """Create login request."""
    return LoginRequestValue(email=email, password=password)


def LoginResponse(
    access_token: str,
    token_type: str = "bearer",  # noqa: S107 - "bearer" is a token type, not a password
    expires_in: int = 900,
) -> LoginResponseValue:
    """Create login response."""
    return LoginResponseValue(
        access_token=access_token, token_type=token_type, expires_in=expires_in
    )


def RegisterRequest(email: str, password: str) -> RegisterRequestValue:
    """Create registration request."""
    return RegisterRequestValue(email=email, password=password)


def RegisterResponse(
    user_id: str, email: str, message: str = "User registered successfully"
) -> RegisterResponseValue:
    """Create registration response."""
    return RegisterResponseValue(user_id=user_id, email=email, message=message)
