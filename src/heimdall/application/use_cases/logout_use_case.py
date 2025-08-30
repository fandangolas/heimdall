"""Logout use case."""

from ...domain.events import UserLoggedOut
from ...domain.repositories import SessionRepository
from ...domain.services import TokenService, EventBus
from ...domain.value_objects import Token, SessionId, UserId


class LogoutUseCase:
    """Use case for user logout."""
    
    def __init__(
        self,
        token_service: TokenService,
        session_repository: SessionRepository,
        event_bus: EventBus,
    ):
        self.token_service = token_service
        self.session_repository = session_repository
        self.event_bus = event_bus
    
    async def execute(self, token_value: str) -> None:
        """Execute the logout use case."""
        # Create token object
        token = Token(token_value)
        
        # Decode token to get session info
        claims = self.token_service.decode_token(token)
        
        # Find and invalidate session
        session_id = SessionId(claims.session_id)
        session = await self.session_repository.find_by_id(session_id)
        
        if session and session.is_valid():
            session.invalidate()
            await self.session_repository.save(session)
            
            # Publish event
            event = UserLoggedOut(
                user_id=UserId(claims.user_id),
                session_id=session_id,
            )
            await self.event_bus.publish(event)