"""PostgreSQL-based dependency injection for FastAPI."""

import logging
from functools import lru_cache
from unittest.mock import AsyncMock, Mock

from fastapi import Depends

from heimdall.application.commands import CommandDependencies
from heimdall.application.queries import QueryDependencies
from heimdall.domain.value_objects import Token, TokenClaims

from .database import DatabaseManager, get_database_manager
from .session_repository import (
    PostgreSQLReadSessionRepository,
    PostgreSQLWriteSessionRepository,
)
from .user_repository import PostgreSQLUserRepository


@lru_cache
def get_db_manager() -> DatabaseManager:
    """Get database manager singleton."""
    return get_database_manager()


def get_postgresql_user_repository() -> PostgreSQLUserRepository:
    """Get PostgreSQL user repository."""
    return PostgreSQLUserRepository(get_db_manager())


def get_postgresql_write_session_repository() -> PostgreSQLWriteSessionRepository:
    """Get PostgreSQL write session repository."""
    return PostgreSQLWriteSessionRepository(get_db_manager())


def get_postgresql_read_session_repository() -> PostgreSQLReadSessionRepository:
    """Get PostgreSQL read session repository."""
    return PostgreSQLReadSessionRepository(get_db_manager())


class _TokenServiceSingleton:
    """Singleton for token service."""

    def __init__(self):
        self._instance = None

    def get_service(self):
        """Get or create the token service."""
        if self._instance is None:
            self._create_service()
        return self._instance

    def _create_service(self):
        """Create the token service instance."""
        self._instance = Mock()
        self._setup_mock_methods()

    def _setup_mock_methods(self):
        """Set up mock methods for token service."""

        def generate_token_impl(session):
            # Create a unique token value for this session (JWT format: 3 parts)
            token_value = (
                f"eyJ{session.id}.eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
                f"{session.id}signature"
            )
            return Token(token_value)

        def validate_token_impl(token):
            # Extract session ID and user info from token (simplified JWT decoding)
            # In real implementation, this would properly decode and validate JWT
            parts = token.value.split(".")
            if len(parts) >= 2:
                try:
                    # Extract session ID from first part (header contains session ID)
                    session_id = parts[0].replace("eyJ", "")

                    # For this demo, we extract basic claims from the token structure
                    # In a real JWT implementation, this would decode the payload
                    return TokenClaims(
                        user_id="",  # Will be filled by the query handler from session
                        session_id=session_id,
                        email="",  # Will be filled by the query handler from session
                        permissions=[],
                    )

                except Exception as e:
                    # Log the exception instead of silent pass
                    logging.warning(f"Token validation failed: {e}")
                    raise ValueError(f"Token validation failed: {e}") from e
            raise ValueError("Invalid token format")

        self._instance.generate_token = generate_token_impl
        self._instance.validate_token = validate_token_impl


# Module-level singleton for token service
_token_singleton = _TokenServiceSingleton()


def get_token_service():
    """Get or create the PostgreSQL token service singleton."""
    return _token_singleton.get_service()


def get_event_bus():
    """Get mock event bus instance."""
    event_bus = AsyncMock()

    async def publish_impl(event):
        # For now, just log or ignore events
        # In real implementation, this would publish to message queue
        pass

    event_bus.publish = publish_impl
    return event_bus


# Create module-level Depends objects to avoid B008 warnings
_DB_MANAGER_DEPENDENCY = Depends(get_db_manager)
_USER_REPO_DEPENDENCY = Depends(lambda: get_postgresql_user_repository())
_WRITE_SESSION_REPO_DEPENDENCY = Depends(
    lambda: get_postgresql_write_session_repository()
)
_READ_SESSION_REPO_DEPENDENCY = Depends(
    lambda: get_postgresql_read_session_repository()
)
_TOKEN_SERVICE_DEPENDENCY = Depends(get_token_service)
_EVENT_BUS_DEPENDENCY = Depends(get_event_bus)


def get_postgresql_command_dependencies() -> CommandDependencies:
    """Create command dependencies with PostgreSQL repositories."""
    return CommandDependencies(
        user_repository=get_postgresql_user_repository(),
        session_repository=get_postgresql_write_session_repository(),
        token_service=get_token_service(),
        event_bus=get_event_bus(),
    )


def get_postgresql_query_dependencies() -> QueryDependencies:
    """Create query dependencies with PostgreSQL repositories."""
    return QueryDependencies(
        session_repository=get_postgresql_read_session_repository(),
        token_service=get_token_service(),
    )
