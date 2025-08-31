"""Authentication command functions (write operations)."""

from typing import NamedTuple

from ...domain.entities import User
from ...domain.events import UserCreated, UserLoggedIn, UserLoggedOut
from ...domain.repositories.write_repositories import (
    WriteSessionRepository,
    WriteUserRepository,
)
from ...domain.services import EventBus, TokenService
from ...domain.value_objects import Email, Password, SessionId, Token
from ..dto import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse


class Dependencies(NamedTuple):
    """Dependencies for command operations (writes)."""

    user_repository: WriteUserRepository
    session_repository: WriteSessionRepository
    token_service: TokenService
    event_bus: EventBus


async def login_user_command(
    request: LoginRequest,
    deps: Dependencies,
) -> LoginResponse:
    """Execute user login command (write operation)."""
    # Parse input
    email = Email(request.email)
    password = Password(request.password)

    # Find user
    user = await deps.user_repository.find_by_email(email)
    if not user:
        raise ValueError("Invalid credentials")

    # Authenticate and create session
    session = user.authenticate(password)

    # Save updated user (last_login_at)
    await deps.user_repository.save(user)

    # Save session
    await deps.session_repository.save(session)

    # Generate token
    token = deps.token_service.generate_token(session)

    # Publish event for read model updates
    event = UserLoggedIn(
        user_id=user.id,
        session_id=session.id,
        email=user.email,
    )
    await deps.event_bus.publish(event)

    return LoginResponse(access_token=token.value)


async def logout_user_command(
    token: Token,
    deps: Dependencies,
) -> None:
    """Execute user logout command (write operation)."""
    # Validate and decode token
    claims = deps.token_service.validate_token(token)

    # Find session
    session_id = SessionId(claims.session_id)
    session = await deps.session_repository.find_by_id(session_id)

    if not session:
        raise ValueError("Session not found")

    if not session.is_valid():
        raise ValueError("Session is invalid")

    # Invalidate session
    session.invalidate()
    await deps.session_repository.save(session)

    # Publish event for read model updates
    event = UserLoggedOut(
        user_id=session.user_id,
        session_id=session.id,
    )
    await deps.event_bus.publish(event)


async def register_user_command(
    request: RegisterRequest,
    deps: Dependencies,
) -> RegisterResponse:
    """Execute user registration command (write operation)."""
    # Parse input
    email = Email(request.email)
    password = Password(request.password)

    # Check if user already exists
    if await deps.user_repository.exists_by_email(email):
        raise ValueError("User with this email already exists")

    # Create new user
    user = User.create(email, password)

    # Save user
    await deps.user_repository.save(user)

    # Publish event for read model updates
    event = UserCreated(user_id=user.id, email=user.email)
    await deps.event_bus.publish(event)

    return RegisterResponse(
        user_id=str(user.id),
        email=str(user.email),
    )
