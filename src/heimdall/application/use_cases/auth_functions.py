"""Authentication use case functions."""

from typing import NamedTuple

from ...domain.entities import User
from ...domain.events import UserCreated, UserLoggedIn, UserLoggedOut
from ...domain.repositories import SessionRepository, UserRepository
from ...domain.services import EventBus, TokenService
from ...domain.value_objects import Email, Password, Token
from ..dto import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse


class Dependencies(NamedTuple):
    """Container for service dependencies."""

    user_repository: UserRepository
    session_repository: SessionRepository
    token_service: TokenService
    event_bus: EventBus


async def login_user(
    request: LoginRequest,
    deps: Dependencies,
) -> LoginResponse:
    """Execute user login use case."""
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

    # Publish event
    event = UserLoggedIn(
        user_id=user.id,
        session_id=session.id,
        email=user.email,
    )
    await deps.event_bus.publish(event)

    return LoginResponse(access_token=token.value)


async def logout_user(
    token: Token,
    deps: Dependencies,
) -> None:
    """Execute user logout use case."""
    # Validate and decode token
    claims = deps.token_service.validate_token(token)

    # Find session
    from ...domain.value_objects import SessionId

    session_id = SessionId(claims.session_id)
    session = await deps.session_repository.find_by_id(session_id)

    if not session:
        raise ValueError("Session not found")

    if not session.is_valid():
        raise ValueError("Session is invalid")

    # Invalidate session
    session.invalidate()
    await deps.session_repository.save(session)

    # Publish event
    event = UserLoggedOut(
        user_id=session.user_id,
        session_id=session.id,
    )
    await deps.event_bus.publish(event)


async def validate_token(
    token: Token,
    deps: Dependencies,
) -> dict:
    """Validate token and return user information."""
    try:
        # Validate and decode token
        claims = deps.token_service.validate_token(token)

        # Check if session exists and is valid
        from ...domain.value_objects import SessionId

        session_id = SessionId(claims.session_id)
        session = await deps.session_repository.find_by_id(session_id)

        if not session or not session.is_valid():
            return {"is_valid": False, "error": "Invalid session"}

        return {
            "is_valid": True,
            "user_id": claims.user_id,
            "email": claims.email,
            "permissions": claims.permissions,
        }

    except Exception as e:
        return {"is_valid": False, "error": str(e)}


async def register_user(
    request: RegisterRequest,
    deps: Dependencies,
) -> RegisterResponse:
    """Execute user registration use case."""
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

    # Publish event
    event = UserCreated(user_id=user.id, email=user.email)
    await deps.event_bus.publish(event)

    return RegisterResponse(
        user_id=str(user.id),
        email=str(user.email),
    )
