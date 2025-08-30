"""Authentication DTOs."""

from dataclasses import dataclass


@dataclass
class LoginRequest:
    """Login request data."""

    email: str
    password: str


@dataclass
class LoginResponse:
    """Login response data."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # in seconds


@dataclass
class RegisterRequest:
    """Registration request data."""

    email: str
    password: str


@dataclass
class RegisterResponse:
    """Registration response data."""

    user_id: str
    email: str
    message: str = "User registered successfully"
