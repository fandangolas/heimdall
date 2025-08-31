"""Tests for CQRS implementation."""

from unittest.mock import AsyncMock, Mock

import pytest

from heimdall.application.commands import (
    CommandDependencies,
    login_user_command,
)
from heimdall.application.cqrs import curry_cqrs_functions
from heimdall.application.dto import LoginRequest
from heimdall.application.queries import QueryDependencies, validate_token_query
from heimdall.domain.entities import User
from heimdall.domain.value_objects import (
    Email,
    Password,
    Token,
    TokenClaims,
    generate_session_id,
)


class TestCQRSCommands:
    """Test CQRS command operations (writes)."""

    @pytest.mark.asyncio
    async def test_login_command_separation(self):
        """Test that login command uses write-optimized dependencies."""
        # Arrange
        request = LoginRequest(email="test@example.com", password="Password123")

        user = User.create(Email("test@example.com"), Password("Password123"))
        session = Mock()
        session.id = generate_session_id()
        user.authenticate = Mock(return_value=session)

        # Write-optimized repositories
        write_user_repo = AsyncMock()
        write_user_repo.find_by_email.return_value = user
        write_user_repo.save = AsyncMock()

        write_session_repo = AsyncMock()
        write_session_repo.save = AsyncMock()

        token_service = Mock()
        token = Token("fake.jwt.token")
        token_service.generate_token.return_value = token

        event_bus = AsyncMock()

        # Command dependencies (write-optimized)
        command_deps = CommandDependencies(
            user_repository=write_user_repo,
            session_repository=write_session_repo,
            token_service=token_service,
            event_bus=event_bus,
        )

        # Act
        response = await login_user_command(request, command_deps)

        # Assert
        assert response.access_token == "fake.jwt.token"
        write_user_repo.find_by_email.assert_called_once()
        write_user_repo.save.assert_called_once()
        write_session_repo.save.assert_called_once()
        event_bus.publish.assert_called_once()


class TestCQRSQueries:
    """Test CQRS query operations (reads)."""

    @pytest.mark.asyncio
    async def test_validate_query_optimized_dependencies(self):
        """Test that validate query uses minimal read-optimized dependencies."""
        # Arrange
        token = Token("fake.jwt.token")
        session_id = generate_session_id()
        claims = TokenClaims(
            user_id="user123",
            session_id=str(session_id),
            email="test@example.com",
            permissions=["read"],
        )

        session = Mock()
        session.is_valid.return_value = True

        # Read-optimized dependencies (minimal)
        read_session_repo = AsyncMock()
        read_session_repo.find_by_id.return_value = session

        token_service = Mock()
        token_service.validate_token.return_value = claims

        # Query dependencies (read-optimized, no user repo or event bus)
        query_deps = QueryDependencies(
            session_repository=read_session_repo,
            token_service=token_service,
        )

        # Act
        result = await validate_token_query(token, query_deps)

        # Assert - minimal operations for performance
        assert result.is_valid is True
        assert result.user_id == "user123"
        read_session_repo.find_by_id.assert_called_once()
        token_service.validate_token.assert_called_once()


class TestCQRSFunctional:
    """Test functional CQRS interface with curried functions."""

    @pytest.mark.asyncio
    async def test_curry_cqrs_functions_creates_partial_functions(self):
        """Test that curry_cqrs_functions creates properly curried functions with CQRS separation."""
        # Arrange - separate dependencies for commands and queries
        command_deps = CommandDependencies(
            user_repository=AsyncMock(),
            session_repository=AsyncMock(),
            token_service=Mock(),
            event_bus=AsyncMock(),
        )

        query_deps = QueryDependencies(
            session_repository=AsyncMock(),  # Different instance, could be cached
            token_service=Mock(),  # Same service, but used differently
        )

        # Act - create curried functions
        cqrs_functions = curry_cqrs_functions(command_deps, query_deps)

        # Assert - verify functional interface
        assert "login" in cqrs_functions  # Command
        assert "register" in cqrs_functions  # Command
        assert "logout" in cqrs_functions  # Command
        assert "validate" in cqrs_functions  # Query

        # Verify these are callable functions
        assert callable(cqrs_functions["login"])
        assert callable(cqrs_functions["validate"])

        # Verify that functions work with just the primary parameter
        # (deps should be baked in via partial application)

        # These should work without needing to pass deps explicitly
        login_func = cqrs_functions["login"]
        validate_func = cqrs_functions["validate"]

        # Functions should be partial objects with deps already applied
        assert hasattr(login_func, "keywords")  # partial objects have this
        assert hasattr(validate_func, "keywords")
        assert "deps" in login_func.keywords
        assert "deps" in validate_func.keywords
