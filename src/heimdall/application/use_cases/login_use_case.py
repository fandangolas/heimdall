"""Login use case."""

from ..dto import LoginRequest, LoginResponse
from ...domain.entities import User
from ...domain.events import UserLoggedIn
from ...domain.repositories import UserRepository, SessionRepository
from ...domain.services import TokenService, EventBus
from ...domain.value_objects import Email, Password


class LoginUseCase:
    """Use case for user login."""
    
    def __init__(
        self,
        user_repository: UserRepository,
        session_repository: SessionRepository,
        token_service: TokenService,
        event_bus: EventBus,
    ):
        self.user_repository = user_repository
        self.session_repository = session_repository
        self.token_service = token_service
        self.event_bus = event_bus
    
    async def execute(self, request: LoginRequest) -> LoginResponse:
        """Execute the login use case."""
        # Parse input
        email = Email(request.email)
        password = Password(request.password)
        
        # Find user
        user = await self.user_repository.find_by_email(email)
        if not user:
            raise ValueError("Invalid credentials")
        
        # Authenticate and create session
        session = user.authenticate(password)
        
        # Save updated user (last_login_at)
        await self.user_repository.save(user)
        
        # Save session
        await self.session_repository.save(session)
        
        # Generate token
        token = self.token_service.generate_token(session)
        
        # Publish event
        event = UserLoggedIn(
            user_id=user.id,
            session_id=session.id,
            email=user.email,
        )
        await self.event_bus.publish(event)
        
        return LoginResponse(access_token=token.value)