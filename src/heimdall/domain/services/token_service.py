"""Token service interface."""

from abc import ABC, abstractmethod

from ..entities import Session
from ..value_objects import Token, TokenClaims


class TokenService(ABC):
    """Abstract interface for token operations."""

    @abstractmethod
    def generate_token(self, session: Session) -> Token:
        """Generate a JWT token from a session."""

    @abstractmethod
    def decode_token(self, token: Token) -> TokenClaims:
        """Decode and validate a JWT token."""

    @abstractmethod
    def refresh_token(self, token: Token) -> Token:
        """Refresh an existing token."""
