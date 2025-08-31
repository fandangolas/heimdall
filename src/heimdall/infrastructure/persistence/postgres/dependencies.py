"""PostgreSQL-based dependency injection for FastAPI."""

import os
from functools import lru_cache
from unittest.mock import Mock

from fastapi import Depends

from heimdall.application.commands import CommandDependencies  
from heimdall.application.queries import QueryDependencies
from heimdall.domain.value_objects import Token, TokenClaims
from .database import DatabaseManager, get_database_manager
from .user_repository import PostgreSQLUserRepository
from .session_repository import (
    PostgreSQLWriteSessionRepository,
    PostgreSQLReadSessionRepository,
)


@lru_cache()
def get_db_manager() -> DatabaseManager:
    """Get database manager singleton."""
    return get_database_manager()


def get_postgresql_user_repository(
    db_manager: DatabaseManager = Depends(get_db_manager),
) -> PostgreSQLUserRepository:
    """Get PostgreSQL user repository."""
    return PostgreSQLUserRepository(db_manager)


def get_postgresql_write_session_repository(
    db_manager: DatabaseManager = Depends(get_db_manager),
) -> PostgreSQLWriteSessionRepository:
    """Get PostgreSQL write session repository."""
    return PostgreSQLWriteSessionRepository(db_manager)


def get_postgresql_read_session_repository(
    db_manager: DatabaseManager = Depends(get_db_manager),
) -> PostgreSQLReadSessionRepository:
    """Get PostgreSQL read session repository."""
    return PostgreSQLReadSessionRepository(db_manager)


# Keep the mock token service for now since we haven't implemented JWT properly yet
_token_service_instance = None


def get_token_service():
    """Get shared mock token service instance."""
    global _token_service_instance
    if _token_service_instance is None:
        _token_service_instance = Mock()
        
        def generate_token_impl(session):
            # Create a unique token value for this session (JWT format: 3 parts)
            token_value = (
                f"eyJ{session.id}.eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
                f"{session.id}signature"
            )
            return Token(token_value)

        def validate_token_impl(token):
            # Extract session ID from token (simplified for demo)
            # In real implementation, this would decode and validate JWT
            parts = token.value.split('.')
            if len(parts) >= 2:
                try:
                    session_id = parts[0].replace('eyJ', '')
                    return TokenClaims(
                        user_id="mock-user-id",
                        session_id=session_id,
                        email="mock@example.com",
                        permissions=[]
                    )
                except Exception:
                    pass
            raise ValueError("Invalid token format")

        _token_service_instance.generate_token = generate_token_impl
        _token_service_instance.validate_token = validate_token_impl

    return _token_service_instance


def get_event_bus():
    """Get mock event bus instance."""
    from unittest.mock import AsyncMock
    
    event_bus = AsyncMock()
    
    async def publish_impl(event):
        # For now, just log or ignore events
        # In real implementation, this would publish to message queue
        pass
    
    event_bus.publish = publish_impl
    return event_bus


def get_postgresql_command_dependencies(
    user_repo=Depends(get_postgresql_user_repository),
    session_repo=Depends(get_postgresql_write_session_repository),
    token_service=Depends(get_token_service),
    event_bus=Depends(get_event_bus),
) -> CommandDependencies:
    """Create command dependencies with PostgreSQL repositories."""
    return CommandDependencies(
        user_repository=user_repo,
        session_repository=session_repo,
        token_service=token_service,
        event_bus=event_bus,
    )


def get_postgresql_query_dependencies(
    session_repo=Depends(get_postgresql_read_session_repository),
    token_service=Depends(get_token_service),
) -> QueryDependencies:
    """Create query dependencies with PostgreSQL repositories."""
    return QueryDependencies(
        session_repository=session_repo,
        token_service=token_service,
    )