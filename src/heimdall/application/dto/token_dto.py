"""Token validation DTOs."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ValidateTokenRequest:
    """Token validation request data."""
    token: str


@dataclass
class ValidateTokenResponse:
    """Token validation response data."""
    is_valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    permissions: Optional[List[str]] = None
    error: Optional[str] = None