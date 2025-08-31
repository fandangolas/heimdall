"""Tests for CQRS error handling and edge cases."""

from unittest.mock import AsyncMock, Mock

import pytest

from heimdall.application.commands import CommandDependencies
from heimdall.application.cqrs import curry_cqrs_functions
from heimdall.application.dto import LoginRequest
from heimdall.application.queries import QueryDependencies
from heimdall.domain.value_objects import Token, TokenClaims, generate_session_id


class TestCQRSErrorHandling:
    """Test error handling in CQRS command and query operations."""

    @pytest.mark.asyncio
    async def test_query_handles_invalid_token_gracefully(self):
        """Test that query operations handle token validation errors gracefully."""
        # Arrange
        token_service = Mock()
        token_service.validate_token.side_effect = ValueError("Invalid token format")

        session_repo = AsyncMock()

        query_deps = QueryDependencies(
            session_repository=session_repo,
            token_service=token_service,
        )

        auth_functions = curry_cqrs_functions(
            CommandDependencies(AsyncMock(), AsyncMock(), Mock(), AsyncMock()),
            query_deps,
        )

        # Act
        token = Token("invalid.jwt.token")
        result = await auth_functions["validate"](token)

        # Assert - Graceful error handling
        assert result.is_valid is False
        assert result.error is not None
        assert "Invalid token format" in result.error

        # Session repository should not be called for invalid tokens
        session_repo.find_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_query_handles_missing_session_gracefully(self):
        """Test that queries handle missing sessions without exceptions."""
        # Arrange
        token_service = Mock()
        session_id = generate_session_id()
        claims = TokenClaims(
            user_id="user123",
            session_id=str(session_id),
            email="test@example.com",
        )
        token_service.validate_token.return_value = claims

        # Session not found in repository
        session_repo = AsyncMock()
        session_repo.find_by_id.return_value = None

        query_deps = QueryDependencies(
            session_repository=session_repo,
            token_service=token_service,
        )

        auth_functions = curry_cqrs_functions(
            CommandDependencies(AsyncMock(), AsyncMock(), Mock(), AsyncMock()),
            query_deps,
        )

        # Act
        token = Token("valid.jwt.token")  # Valid JWT format
        result = await auth_functions["validate"](token)

        # Assert - Should handle gracefully
        assert result.is_valid is False
        assert result.error == "Invalid session"

    @pytest.mark.asyncio
    async def test_query_handles_expired_session_gracefully(self):
        """Test that queries handle expired/invalid sessions properly."""
        # Arrange
        token_service = Mock()
        session_id = generate_session_id()
        claims = TokenClaims(
            user_id="user123",
            session_id=str(session_id),
            email="test@example.com",
        )
        token_service.validate_token.return_value = claims

        # Session exists but is invalid/expired
        expired_session = Mock()
        expired_session.is_valid.return_value = False

        session_repo = AsyncMock()
        session_repo.find_by_id.return_value = expired_session

        query_deps = QueryDependencies(
            session_repository=session_repo,
            token_service=token_service,
        )

        auth_functions = curry_cqrs_functions(
            CommandDependencies(AsyncMock(), AsyncMock(), Mock(), AsyncMock()),
            query_deps,
        )

        # Act
        token = Token("expired.session.token")
        result = await auth_functions["validate"](token)

        # Assert - Should reject expired sessions
        assert result.is_valid is False
        assert result.error == "Invalid session"

    @pytest.mark.asyncio
    async def test_command_error_isolation_from_queries(self):
        """Test that command-side errors don't affect query operations."""
        # Arrange - Broken command dependencies
        broken_user_repo = AsyncMock()
        broken_user_repo.find_by_email.side_effect = Exception(
            "Database connection failed"
        )

        broken_event_bus = AsyncMock()
        broken_event_bus.publish.side_effect = Exception("Event bus down")

        command_deps = CommandDependencies(
            user_repository=broken_user_repo,
            session_repository=AsyncMock(),
            token_service=Mock(),
            event_bus=broken_event_bus,
        )

        # Working query dependencies
        token_service = Mock()
        session_id = generate_session_id()
        claims = TokenClaims("user123", str(session_id), "test@example.com")
        token_service.validate_token.return_value = claims

        session = Mock()
        session.is_valid.return_value = True

        session_repo = AsyncMock()
        session_repo.find_by_id.return_value = session

        query_deps = QueryDependencies(
            session_repository=session_repo,
            token_service=token_service,
        )

        auth_functions = curry_cqrs_functions(command_deps, query_deps)

        # Act - Query should work despite broken command dependencies
        token = Token("working.jwt.token")  # Valid JWT format
        result = await auth_functions["validate"](token)

        # Assert - Query isolation from command failures
        assert result.is_valid is True
        assert result.user_id == "user123"

        # Commands would fail, but queries are isolated
        login_request = LoginRequest(email="test@example.com", password="Password123")
        with pytest.raises(Exception, match="Database connection failed"):
            await auth_functions["login"](login_request)

    @pytest.mark.asyncio
    async def test_partial_function_error_handling(self):
        """Test that curried functions handle dependency injection errors properly."""
        # Arrange - Invalid dependencies (None instead of proper deps)
        invalid_command_deps = None
        valid_query_deps = QueryDependencies(
            session_repository=AsyncMock(),
            token_service=Mock(),
        )

        # Act & Assert - Should fail when trying to use the invalid dependencies
        with pytest.raises(AttributeError):
            auth_functions = curry_cqrs_functions(
                invalid_command_deps, valid_query_deps
            )
            # The error occurs when trying to access attributes of None
            await auth_functions["login"](
                LoginRequest(email="test@test.com", password="Password123")
            )

    @pytest.mark.asyncio
    async def test_concurrent_query_error_isolation(self):
        """Test that errors in one query don't affect other concurrent queries."""
        # Arrange
        token_service = Mock()

        # Setup different behaviors for different tokens
        def validate_token_side_effect(token):
            if token.value == "bad.jwt.token":
                raise ValueError("Bad token")
            session_id = generate_session_id()
            return TokenClaims("user123", str(session_id), "test@example.com")

        token_service.validate_token.side_effect = validate_token_side_effect

        session = Mock()
        session.is_valid.return_value = True

        session_repo = AsyncMock()
        session_repo.find_by_id.return_value = session

        query_deps = QueryDependencies(
            session_repository=session_repo,
            token_service=token_service,
        )

        auth_functions = curry_cqrs_functions(
            CommandDependencies(AsyncMock(), AsyncMock(), Mock(), AsyncMock()),
            query_deps,
        )

        # Act - Concurrent queries with one failing
        import asyncio

        good_token = Token("good.jwt.token")  # Valid JWT format
        bad_token = Token("bad.jwt.token")  # Valid JWT format

        good_result, bad_result = await asyncio.gather(
            auth_functions["validate"](good_token),
            auth_functions["validate"](bad_token),
            return_exceptions=False,  # Don't stop on exceptions
        )

        # Assert - Good query succeeds despite bad query failing
        assert good_result.is_valid is True
        assert bad_result.is_valid is False
        assert "Bad token" in bad_result.error
