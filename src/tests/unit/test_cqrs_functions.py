"""Tests for CQRS functional implementation."""

from unittest.mock import AsyncMock, Mock

import pytest

from heimdall.application.commands import (
    CommandDependencies,
    login_user_command,
    register_user_command,
)
from heimdall.application.dto import LoginRequest, RegisterRequest
from heimdall.application.queries import QueryDependencies, validate_token_query
from heimdall.domain.entities import User
from heimdall.domain.value_objects import (
    Email,
    Password,
    Token,
    TokenClaims,
    generate_session_id,
)


class TestFunctionalLogin:
    """Test functional login use case."""

    @pytest.mark.asyncio
    async def test_successful_login(self):
        """Test successful user login."""
        # Arrange
        request = LoginRequest(email="test@example.com", password="Password123")

        user = User.create(Email("test@example.com"), Password("Password123"))
        session = Mock()
        session.id = generate_session_id()

        # Mock authenticate to return our session
        user.authenticate = Mock(return_value=session)

        # Create mocks
        user_repo = AsyncMock()
        user_repo.find_by_email.return_value = user
        user_repo.save = AsyncMock()

        session_repo = AsyncMock()
        session_repo.save = AsyncMock()

        token_service = Mock()
        token = Token("fake.jwt.token")
        token_service.generate_token.return_value = token

        event_bus = AsyncMock()
        event_bus.publish = AsyncMock()

        # Create command dependencies
        command_deps = CommandDependencies(
            user_repository=user_repo,
            session_repository=session_repo,
            token_service=token_service,
            event_bus=event_bus,
        )

        # Act
        response = await login_user_command(request, command_deps)

        # Assert
        assert response.access_token == "fake.jwt.token"
        user_repo.find_by_email.assert_called_once_with(Email("test@example.com"))
        user.authenticate.assert_called_once_with(Password("Password123"))
        user_repo.save.assert_called_once_with(user)
        session_repo.save.assert_called_once_with(session)
        token_service.generate_token.assert_called_once_with(session)
        event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_user_not_found(self):
        """Test login with non-existent user."""
        # Arrange
        request = LoginRequest(email="test@example.com", password="Password123")

        user_repo = AsyncMock()
        user_repo.find_by_email.return_value = None

        session_repo = AsyncMock()
        token_service = Mock()
        event_bus = AsyncMock()

        # Create command dependencies
        command_deps = CommandDependencies(
            user_repository=user_repo,
            session_repository=session_repo,
            token_service=token_service,
            event_bus=event_bus,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid credentials"):
            await login_user_command(request, command_deps)


class TestFunctionalRegister:
    """Test functional register use case."""

    @pytest.mark.asyncio
    async def test_successful_registration(self):
        """Test successful user registration."""
        # Arrange
        request = RegisterRequest(email="test@example.com", password="Password123")

        user_repo = AsyncMock()
        user_repo.exists_by_email.return_value = False
        user_repo.save = AsyncMock()

        event_bus = AsyncMock()
        event_bus.publish = AsyncMock()

        # Create command dependencies
        command_deps = CommandDependencies(
            user_repository=user_repo,
            session_repository=AsyncMock(),  # Not used in register
            token_service=Mock(),  # Not used in register
            event_bus=event_bus,
        )

        # Act
        response = await register_user_command(request, command_deps)

        # Assert
        assert response.email == "test@example.com"
        assert response.user_id  # Should have a user ID
        user_repo.exists_by_email.assert_called_once_with(Email("test@example.com"))
        user_repo.save.assert_called_once()
        event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_registration_existing_email(self):
        """Test registration with existing email."""
        # Arrange
        request = RegisterRequest(email="test@example.com", password="Password123")

        user_repo = AsyncMock()
        user_repo.exists_by_email.return_value = True

        event_bus = AsyncMock()

        # Create command dependencies
        command_deps = CommandDependencies(
            user_repository=user_repo,
            session_repository=AsyncMock(),  # Not used in register
            token_service=Mock(),  # Not used in register
            event_bus=event_bus,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="User with this email already exists"):
            await register_user_command(request, command_deps)


class TestFunctionalValidateToken:
    """Test functional validate token use case."""

    @pytest.mark.asyncio
    async def test_valid_token(self):
        """Test validating a valid token."""
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

        token_service = Mock()
        token_service.validate_token.return_value = claims

        session_repo = AsyncMock()
        session_repo.find_by_id.return_value = session

        # Create query dependencies (optimized for reads)
        query_deps = QueryDependencies(
            session_repository=session_repo,
            token_service=token_service,
        )

        # Act
        result = await validate_token_query(token, query_deps)

        # Assert
        assert result.is_valid is True
        assert result.user_id == "user123"
        assert result.email == "test@example.com"
        assert result.permissions == ("read",)

    @pytest.mark.asyncio
    async def test_invalid_session(self):
        """Test validating token with invalid session."""
        # Arrange
        token = Token("fake.jwt.token")
        session_id = generate_session_id()
        claims = TokenClaims(
            user_id="user123", session_id=str(session_id), email="test@example.com"
        )

        token_service = Mock()
        token_service.validate_token.return_value = claims

        session_repo = AsyncMock()
        session_repo.find_by_id.return_value = None

        # Create query dependencies (optimized for reads)
        query_deps = QueryDependencies(
            session_repository=session_repo,
            token_service=token_service,
        )

        # Act
        result = await validate_token_query(token, query_deps)

        # Assert
        assert result.is_valid is False
        assert result.error == "Invalid session"
