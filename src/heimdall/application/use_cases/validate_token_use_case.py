"""Validate token use case."""

from ..dto import ValidateTokenRequest, ValidateTokenResponse
from ...domain.repositories import SessionRepository
from ...domain.services import TokenService
from ...domain.value_objects import Token, SessionId


class ValidateTokenUseCase:
    """Use case for token validation."""
    
    def __init__(
        self,
        token_service: TokenService,
        session_repository: SessionRepository,
    ):
        self.token_service = token_service
        self.session_repository = session_repository
    
    async def execute(self, request: ValidateTokenRequest) -> ValidateTokenResponse:
        """Execute the token validation use case."""
        try:
            # Create token object
            token = Token(request.token)
            
            # Decode and validate token
            claims = self.token_service.decode_token(token)
            
            # Check if token is expired
            if claims.is_expired():
                return ValidateTokenResponse(
                    is_valid=False,
                    error="Token has expired"
                )
            
            # Check if session is still valid
            session_id = SessionId(claims.session_id)
            session = await self.session_repository.find_by_id(session_id)
            
            if not session or not session.is_valid():
                return ValidateTokenResponse(
                    is_valid=False,
                    error="Session is invalid or expired"
                )
            
            return ValidateTokenResponse(
                is_valid=True,
                user_id=claims.user_id,
                email=claims.email,
                permissions=claims.permissions,
            )
            
        except Exception as e:
            return ValidateTokenResponse(
                is_valid=False,
                error=str(e)
            )