"""Register use case."""

from ..dto import RegisterRequest, RegisterResponse
from ...domain.entities import User
from ...domain.events import UserCreated
from ...domain.repositories import UserRepository
from ...domain.services import EventBus
from ...domain.value_objects import Email, Password


class RegisterUseCase:
    """Use case for user registration."""
    
    def __init__(
        self,
        user_repository: UserRepository,
        event_bus: EventBus,
    ):
        self.user_repository = user_repository
        self.event_bus = event_bus
    
    async def execute(self, request: RegisterRequest) -> RegisterResponse:
        """Execute the registration use case."""
        # Parse input
        email = Email(request.email)
        password = Password(request.password)
        
        # Check if user already exists
        if await self.user_repository.exists_by_email(email):
            raise ValueError("User with this email already exists")
        
        # Create new user
        user = User.create(email, password)
        
        # Save user
        await self.user_repository.save(user)
        
        # Publish event
        event = UserCreated(user_id=user.id, email=user.email)
        await self.event_bus.publish(event)
        
        return RegisterResponse(
            user_id=str(user.id),
            email=str(user.email),
        )