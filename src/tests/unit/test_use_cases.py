"""Tests for use cases."""

import pytest
from unittest.mock import AsyncMock, Mock

from heimdall.application.dto import (
    LoginRequest, LoginResponse, RegisterRequest, RegisterResponse,
    ValidateTokenRequest, ValidateTokenResponse
)
from heimdall.application.use_cases import (
    LoginUseCase, RegisterUseCase, ValidateTokenUseCase, LogoutUseCase
)
from heimdall.domain.entities import User, Session
from heimdall.domain.events import UserCreated, UserLoggedIn, UserLoggedOut
from heimdall.domain.value_objects import (
    Email, Password, UserId, SessionId, Token, TokenClaims
)


class TestLoginUseCase:
    """Test LoginUseCase."""
    
    @pytest.fixture
    def user_repository(self):
        """Mock user repository."""
        return AsyncMock()
    
    @pytest.fixture
    def session_repository(self):
        """Mock session repository."""
        return AsyncMock()
    
    @pytest.fixture
    def token_service(self):
        """Mock token service."""
        return Mock()
    
    @pytest.fixture
    def event_bus(self):
        """Mock event bus."""
        return AsyncMock()
    
    @pytest.fixture
    def login_use_case(self, user_repository, session_repository, token_service, event_bus):
        """Create LoginUseCase instance."""
        return LoginUseCase(
            user_repository=user_repository,
            session_repository=session_repository,
            token_service=token_service,
            event_bus=event_bus
        )
    
    @pytest.mark.asyncio
    async def test_successful_login(self, login_use_case, user_repository, session_repository, token_service, event_bus):
        """Test successful login."""
        # Arrange
        email = Email("test@example.com")
        password = Password("ValidPass123")
        user = User.create(email, password)
        token = Token("header.payload.signature")
        
        user_repository.find_by_email.return_value = user
        token_service.generate_token.return_value = token
        
        request = LoginRequest(email="test@example.com", password="ValidPass123")
        
        # Act
        response = await login_use_case.execute(request)
        
        # Assert
        assert isinstance(response, LoginResponse)
        assert response.access_token == token.value
        assert response.token_type == "bearer"
        
        # Verify repository calls
        user_repository.find_by_email.assert_called_once_with(email)
        user_repository.save.assert_called_once_with(user)
        session_repository.save.assert_called_once()
        
        # Verify token service call
        token_service.generate_token.assert_called_once()
        
        # Verify event publishing
        event_bus.publish.assert_called_once()
        published_event = event_bus.publish.call_args[0][0]
        assert isinstance(published_event, UserLoggedIn)
        assert published_event.user_id == user.id
        assert published_event.email == user.email
    
    @pytest.mark.asyncio
    async def test_login_user_not_found(self, login_use_case, user_repository):
        """Test login with non-existent user."""
        # Arrange
        user_repository.find_by_email.return_value = None
        request = LoginRequest(email="nonexistent@example.com", password="ValidPass123")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid credentials"):
            await login_use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, login_use_case, user_repository):
        """Test login with invalid password."""
        # Arrange
        email = Email("test@example.com")
        password = Password("ValidPass123")
        user = User.create(email, password)
        
        user_repository.find_by_email.return_value = user
        request = LoginRequest(email="test@example.com", password="WrongPass456")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid credentials"):
            await login_use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, login_use_case, user_repository):
        """Test login with inactive user."""
        # Arrange
        email = Email("test@example.com")
        password = Password("ValidPass123")
        user = User.create(email, password)
        user.deactivate()
        
        user_repository.find_by_email.return_value = user
        request = LoginRequest(email="test@example.com", password="ValidPass123")
        
        # Act & Assert
        with pytest.raises(ValueError, match="User account is inactive"):
            await login_use_case.execute(request)


class TestRegisterUseCase:
    """Test RegisterUseCase."""
    
    @pytest.fixture
    def user_repository(self):
        """Mock user repository."""
        return AsyncMock()
    
    @pytest.fixture
    def event_bus(self):
        """Mock event bus."""
        return AsyncMock()
    
    @pytest.fixture
    def register_use_case(self, user_repository, event_bus):
        """Create RegisterUseCase instance."""
        return RegisterUseCase(
            user_repository=user_repository,
            event_bus=event_bus
        )
    
    @pytest.mark.asyncio
    async def test_successful_registration(self, register_use_case, user_repository, event_bus):
        """Test successful user registration."""
        # Arrange
        user_repository.exists_by_email.return_value = False
        request = RegisterRequest(email="test@example.com", password="ValidPass123")
        
        # Act
        response = await register_use_case.execute(request)
        
        # Assert
        assert isinstance(response, RegisterResponse)
        assert response.email == "test@example.com"
        assert len(response.user_id) == 36  # UUID format
        assert response.message == "User registered successfully"
        
        # Verify repository calls
        user_repository.exists_by_email.assert_called_once()
        user_repository.save.assert_called_once()
        
        # Verify event publishing
        event_bus.publish.assert_called_once()
        published_event = event_bus.publish.call_args[0][0]
        assert isinstance(published_event, UserCreated)
        assert published_event.email.value == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_registration_existing_email(self, register_use_case, user_repository):
        """Test registration with existing email."""
        # Arrange
        user_repository.exists_by_email.return_value = True
        request = RegisterRequest(email="existing@example.com", password="ValidPass123")
        
        # Act & Assert
        with pytest.raises(ValueError, match="User with this email already exists"):
            await register_use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_registration_invalid_email(self, register_use_case, user_repository):
        """Test registration with invalid email."""
        # Arrange
        request = RegisterRequest(email="invalid-email", password="ValidPass123")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email format"):
            await register_use_case.execute(request)
    
    @pytest.mark.asyncio
    async def test_registration_weak_password(self, register_use_case, user_repository):
        """Test registration with weak password."""
        # Arrange
        request = RegisterRequest(email="test@example.com", password="weak")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Password must be at least"):
            await register_use_case.execute(request)


class TestValidateTokenUseCase:
    """Test ValidateTokenUseCase."""
    
    @pytest.fixture
    def token_service(self):
        """Mock token service."""
        return Mock()
    
    @pytest.fixture
    def session_repository(self):
        """Mock session repository."""
        return AsyncMock()
    
    @pytest.fixture
    def validate_token_use_case(self, token_service, session_repository):
        """Create ValidateTokenUseCase instance."""
        return ValidateTokenUseCase(
            token_service=token_service,
            session_repository=session_repository
        )
    
    @pytest.mark.asyncio
    async def test_valid_token(self, validate_token_use_case, token_service, session_repository):
        """Test validating a valid token."""
        # Arrange
        user_id = UserId.generate()
        session_id = SessionId.generate()
        email = Email("test@example.com")
        
        claims = TokenClaims(
            user_id=str(user_id),
            session_id=str(session_id),
            email=str(email),
            permissions=["read", "write"]
        )
        session = Session.create_for_user(user_id, email, ["read", "write"])
        
        token_service.decode_token.return_value = claims
        session_repository.find_by_id.return_value = session
        
        request = ValidateTokenRequest(token="header.payload.signature")
        
        # Act
        response = await validate_token_use_case.execute(request)
        
        # Assert
        assert response.is_valid is True
        assert response.user_id == str(user_id)
        assert response.email == str(email)
        assert response.permissions == ["read", "write"]
        assert response.error is None
        
        # Verify service calls
        token_service.decode_token.assert_called_once()
        session_repository.find_by_id.assert_called_once_with(session_id)
    
    @pytest.mark.asyncio
    async def test_expired_token(self, validate_token_use_case, token_service, session_repository):
        """Test validating an expired token."""
        # Arrange
        from datetime import datetime, timezone, timedelta
        
        claims = TokenClaims(
            user_id="user-123",
            session_id="session-456",
            email="test@example.com",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
        )
        
        token_service.decode_token.return_value = claims
        
        request = ValidateTokenRequest(token="header.payload.signature")
        
        # Act
        response = await validate_token_use_case.execute(request)
        
        # Assert
        assert response.is_valid is False
        assert response.error == "Token has expired"
        
        # Should not check session if token is expired
        session_repository.find_by_id.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_invalid_session(self, validate_token_use_case, token_service, session_repository):
        """Test validating token with invalid session."""
        # Arrange
        session_id = SessionId.generate()
        claims = TokenClaims(
            user_id=str(UserId.generate()),
            session_id=str(session_id),
            email="test@example.com"
        )
        
        token_service.decode_token.return_value = claims
        session_repository.find_by_id.return_value = None  # Session not found
        
        request = ValidateTokenRequest(token="header.payload.signature")
        
        # Act
        response = await validate_token_use_case.execute(request)
        
        # Assert
        assert response.is_valid is False
        assert response.error == "Session is invalid or expired"
    
    @pytest.mark.asyncio
    async def test_malformed_token(self, validate_token_use_case, token_service):
        """Test validating malformed token."""
        # Arrange
        token_service.decode_token.side_effect = ValueError("Invalid token format")
        
        request = ValidateTokenRequest(token="invalid.token")
        
        # Act
        response = await validate_token_use_case.execute(request)
        
        # Assert
        assert response.is_valid is False
        assert "Invalid token format" in response.error


class TestLogoutUseCase:
    """Test LogoutUseCase."""
    
    @pytest.fixture
    def token_service(self):
        """Mock token service."""
        return Mock()
    
    @pytest.fixture
    def session_repository(self):
        """Mock session repository."""
        return AsyncMock()
    
    @pytest.fixture
    def event_bus(self):
        """Mock event bus."""
        return AsyncMock()
    
    @pytest.fixture
    def logout_use_case(self, token_service, session_repository, event_bus):
        """Create LogoutUseCase instance."""
        return LogoutUseCase(
            token_service=token_service,
            session_repository=session_repository,
            event_bus=event_bus
        )
    
    @pytest.mark.asyncio
    async def test_successful_logout(self, logout_use_case, token_service, session_repository, event_bus):
        """Test successful logout."""
        # Arrange
        user_id = UserId.generate()
        session_id = SessionId.generate()
        email = Email("test@example.com")
        
        claims = TokenClaims(
            user_id=str(user_id),
            session_id=str(session_id),
            email=str(email)
        )
        session = Session.create_for_user(user_id, email, [])
        
        token_service.decode_token.return_value = claims
        session_repository.find_by_id.return_value = session
        
        # Act
        await logout_use_case.execute("header.payload.signature")
        
        # Assert
        assert session.is_active is False
        
        # Verify repository calls
        session_repository.find_by_id.assert_called_once_with(session_id)
        session_repository.save.assert_called_once_with(session)
        
        # Verify event publishing
        event_bus.publish.assert_called_once()
        published_event = event_bus.publish.call_args[0][0]
        assert isinstance(published_event, UserLoggedOut)
        assert published_event.user_id == user_id
        assert published_event.session_id == session_id
    
    @pytest.mark.asyncio
    async def test_logout_nonexistent_session(self, logout_use_case, token_service, session_repository, event_bus):
        """Test logout with nonexistent session."""
        # Arrange
        claims = TokenClaims(
            user_id=str(UserId.generate()),
            session_id=str(SessionId.generate()),
            email="test@example.com"
        )
        
        token_service.decode_token.return_value = claims
        session_repository.find_by_id.return_value = None
        
        # Act
        await logout_use_case.execute("header.payload.signature")
        
        # Assert - should not crash, just do nothing
        session_repository.save.assert_not_called()
        event_bus.publish.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_logout_already_invalid_session(self, logout_use_case, token_service, session_repository, event_bus):
        """Test logout with already invalidated session."""
        # Arrange
        user_id = UserId.generate()
        session_id = SessionId.generate()
        email = Email("test@example.com")
        
        claims = TokenClaims(
            user_id=str(user_id),
            session_id=str(session_id),
            email=str(email)
        )
        session = Session.create_for_user(user_id, email, [])
        session.invalidate()  # Already invalidated
        
        token_service.decode_token.return_value = claims
        session_repository.find_by_id.return_value = session
        
        # Act
        await logout_use_case.execute("header.payload.signature")
        
        # Assert - should not save or publish event for already invalid session
        session_repository.save.assert_not_called()
        event_bus.publish.assert_not_called()