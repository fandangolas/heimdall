"""FastAPI dependency injection setup for CQRS functions."""

import os
from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, Mock

from fastapi import Depends

from heimdall.application.commands import CommandDependencies
from heimdall.application.cqrs import curry_cqrs_functions
from heimdall.application.queries import QueryDependencies
from heimdall.domain.entities import Session, User
from heimdall.domain.value_objects import Token, TokenClaims


def get_persistence_mode() -> str:
    """Get persistence mode from environment variable."""
    return os.getenv("PERSISTENCE_MODE", "in-memory").lower()


def should_use_postgres() -> bool:
    """Check if PostgreSQL should be used based on persistence mode."""
    persistence_mode = get_persistence_mode()
    return persistence_mode == "postgres"

# Global in-memory storage for demo/testing (would be replaced with real DB)
_USERS: dict[str, User] = {}
_SESSIONS: dict[str, Session] = {}
_EVENTS: list = []
_TOKEN_TO_SESSION: dict[str, str] = {}  # Maps token values to session IDs


_token_service_instance = None


def get_token_service():
    """Get shared mock token service instance."""
    global _token_service_instance  # noqa: PLW0603
    if _token_service_instance is None:
        _token_service_instance = Mock()

        def generate_token_impl(session):
            # Create a unique token value for this session (JWT format: 3 parts)
            token_value = (
                f"eyJ{session.id}.eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
                f"{session.id}signature"
            )
            # Map token to session for validation
            _TOKEN_TO_SESSION[token_value] = str(session.id)
            return Token(token_value)

        def validate_token_impl(token):
            # Simple validation for demo - in production would decode JWT
            if token.value in _TOKEN_TO_SESSION:
                # Find the correct session for this token
                session_id = _TOKEN_TO_SESSION[token.value]
                session = _SESSIONS.get(session_id)
                if session:
                    return TokenClaims(
                        user_id=str(session.user_id),
                        session_id=str(session.id),
                        email=str(session.email),
                        permissions=list(session.permissions)
                        if hasattr(session, "permissions")
                        else [],
                    )
            raise ValueError("Invalid token format")

        _token_service_instance.generate_token = generate_token_impl
        _token_service_instance.validate_token = validate_token_impl

    return _token_service_instance


def get_event_bus():
    """Get mock event bus instance."""
    event_bus = AsyncMock()

    async def publish_impl(event):
        _EVENTS.append(event)

    event_bus.publish = publish_impl
    return event_bus


def get_user_repository():
    """Get mock user repository instance."""
    user_repo = AsyncMock()

    async def find_by_email_impl(email):
        return _USERS.get(str(email))

    async def exists_by_email_impl(email):
        return str(email) in _USERS

    async def save_impl(user):
        _USERS[str(user.email)] = user

    async def find_by_id_impl(user_id):
        for user in _USERS.values():
            if str(user.id) == str(user_id):
                return user
        return None

    user_repo.find_by_email = find_by_email_impl
    user_repo.exists_by_email = exists_by_email_impl
    user_repo.save = save_impl
    user_repo.find_by_id = find_by_id_impl
    return user_repo


def get_session_repository():
    """Get mock session repository instance."""
    session_repo = AsyncMock()

    async def find_by_id_impl(session_id):
        return _SESSIONS.get(str(session_id))

    async def save_impl(session):
        _SESSIONS[str(session.id)] = session

    session_repo.find_by_id = find_by_id_impl
    session_repo.save = save_impl
    return session_repo


# Create module-level Depends objects to avoid B008 warnings
_USER_REPO_DEPENDENCY = Depends(get_user_repository)
_SESSION_REPO_DEPENDENCY = Depends(get_session_repository)
_TOKEN_SERVICE_DEPENDENCY = Depends(get_token_service)
_EVENT_BUS_DEPENDENCY = Depends(get_event_bus)


def get_command_dependencies(
    user_repo=_USER_REPO_DEPENDENCY,
    session_repo=_SESSION_REPO_DEPENDENCY,
    token_service=_TOKEN_SERVICE_DEPENDENCY,
    event_bus=_EVENT_BUS_DEPENDENCY,
) -> CommandDependencies:
    """Create command dependencies for write operations."""
    return CommandDependencies(
        user_repository=user_repo,
        session_repository=session_repo,
        token_service=token_service,
        event_bus=event_bus,
    )


def get_query_dependencies(
    session_repo=_SESSION_REPO_DEPENDENCY,
    token_service=_TOKEN_SERVICE_DEPENDENCY,
) -> QueryDependencies:
    """Create query dependencies for read operations (minimal dependencies)."""
    return QueryDependencies(
        session_repository=session_repo,
        token_service=token_service,
    )


def _get_postgresql_dependencies():
    """Try to get PostgreSQL dependencies."""
    try:
        from heimdall.infrastructure.persistence.postgres.dependencies import (
            get_postgresql_command_dependencies,
            get_postgresql_query_dependencies,
        )

        return get_postgresql_command_dependencies, get_postgresql_query_dependencies
    except ImportError:
        return None, None


def get_dynamic_command_dependencies() -> CommandDependencies:
    """Get command dependencies based on persistence mode."""
    if should_use_postgres():
        postgres_cmd_deps, _ = _get_postgresql_dependencies()
        if postgres_cmd_deps:
            return postgres_cmd_deps()
    # Fallback to mock dependencies
    return get_command_dependencies()


def get_dynamic_query_dependencies() -> QueryDependencies:
    """Get query dependencies based on persistence mode."""
    if should_use_postgres():
        _, postgres_query_deps = _get_postgresql_dependencies()
        if postgres_query_deps:
            return postgres_query_deps()
    # Fallback to mock dependencies  
    return get_query_dependencies()


# Create dependencies for auth functions - these will dynamically select the right backend
_COMMAND_DEPS_DEPENDENCY = Depends(get_dynamic_command_dependencies)
_QUERY_DEPS_DEPENDENCY = Depends(get_dynamic_query_dependencies)


def get_auth_functions(
    command_deps: CommandDependencies = _COMMAND_DEPS_DEPENDENCY,
    query_deps: QueryDependencies = _QUERY_DEPS_DEPENDENCY,
) -> dict[str, Callable[..., Any]]:
    """Get curried CQRS auth functions with dynamic backend selection."""
    persistence_mode = get_persistence_mode()
    print(f"🔧 Using persistence mode: {persistence_mode}")
    
    return curry_cqrs_functions(command_deps, query_deps)
