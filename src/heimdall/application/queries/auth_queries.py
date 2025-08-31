"""Authentication query functions (read operations)."""

from typing import NamedTuple

from ...domain.repositories.read_repositories import ReadSessionRepository
from ...domain.services import TokenService
from ...domain.value_objects import SessionId, Token
from ..dto import ValidateTokenResponse


class Dependencies(NamedTuple):
    """Dependencies for query operations (reads) - optimized for performance."""

    session_repository: ReadSessionRepository
    token_service: TokenService
    # Note: No user_repository or event_bus needed for reads


async def validate_token_query(
    token: Token,
    deps: Dependencies,
) -> ValidateTokenResponse:
    """Validate token query (read operation) - optimized for performance."""
    try:
        # Fast token validation
        claims = deps.token_service.validate_token(token)

        # Fast session lookup (could be cached in future)
        session_id = SessionId(claims.session_id)
        session = await deps.session_repository.find_by_id(session_id)

        if not session or not session.is_valid():
            return ValidateTokenResponse(is_valid=False, error="Invalid session")

        # Return minimal data needed for authorization
        return ValidateTokenResponse(
            is_valid=True,
            user_id=claims.user_id,
            email=claims.email,
            permissions=list(claims.permissions) if claims.permissions else [],
        )

    except Exception as e:
        return ValidateTokenResponse(is_valid=False, error=str(e))
