"""Authentication DTOs."""

from dataclasses import dataclass
# No typing imports needed - using built-in types


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
    expires_in: int = 900  # 15 minutes in seconds


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