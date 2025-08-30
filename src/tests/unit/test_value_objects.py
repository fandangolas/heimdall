"""Tests for value objects."""

import pytest
from datetime import datetime, timezone, timedelta

from heimdall.domain.value_objects import (
    Email, Password, PasswordHash, Token, TokenClaims, UserId, SessionId
)


class TestEmail:
    """Test Email value object."""
    
    def test_valid_email(self):
        """Test valid email creation."""
        email = Email("test@example.com")
        assert email.value == "test@example.com"
        assert str(email) == "test@example.com"
    
    def test_email_normalization(self):
        """Test email is normalized to lowercase."""
        email = Email("TEST@Example.COM")
        assert email.value == "test@example.com"
    
    def test_domain_extraction(self):
        """Test domain extraction."""
        email = Email("user@domain.com")
        assert email.domain() == "domain.com"
    
    def test_invalid_email_format(self):
        """Test invalid email formats raise ValueError."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("invalid-email")
        
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("@domain.com")
        
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("user@")
    
    def test_empty_email(self):
        """Test empty email raises ValueError."""
        with pytest.raises(ValueError, match="Email cannot be empty"):
            Email("")


class TestPassword:
    """Test Password value object."""
    
    def test_valid_password(self):
        """Test valid password creation."""
        password = Password("ValidPass123")
        assert password.value == "ValidPass123"
        assert str(password) == "********"  # Masked representation
    
    def test_password_hashing(self):
        """Test password hashing."""
        password = Password("ValidPass123")
        hash_obj = password.hash()
        assert isinstance(hash_obj, PasswordHash)
        assert hash_obj.value != password.value
        assert hash_obj.verify(password) is True
    
    def test_short_password(self):
        """Test password too short raises ValueError."""
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            Password("short")
    
    def test_password_without_uppercase(self):
        """Test password without uppercase raises ValueError."""
        with pytest.raises(ValueError, match="Password must contain at least one uppercase"):
            Password("lowercase123")
    
    def test_password_without_lowercase(self):
        """Test password without lowercase raises ValueError."""
        with pytest.raises(ValueError, match="Password must contain at least one uppercase"):
            Password("UPPERCASE123")
    
    def test_password_without_digit(self):
        """Test password without digit raises ValueError."""
        with pytest.raises(ValueError, match="Password must contain at least one uppercase"):
            Password("NoDigitsHere")
    
    def test_empty_password(self):
        """Test empty password raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            Password("")


class TestPasswordHash:
    """Test PasswordHash value object."""
    
    def test_valid_hash(self):
        """Test valid hash creation."""
        hash_value = "$2b$12$abcdefghijklmnopqrstuvwxyz"
        hash_obj = PasswordHash(hash_value)
        assert hash_obj.value == hash_value
        assert "...uvwxyz" in str(hash_obj)
    
    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = Password("ValidPass123")
        hash_obj = password.hash()
        assert hash_obj.verify(password) is True
    
    def test_verify_incorrect_password(self):
        """Test verifying incorrect password."""
        password = Password("ValidPass123")
        wrong_password = Password("WrongPass456")
        hash_obj = password.hash()
        assert hash_obj.verify(wrong_password) is False
    
    def test_empty_hash(self):
        """Test empty hash raises ValueError."""
        with pytest.raises(ValueError, match="Password hash cannot be empty"):
            PasswordHash("")


class TestUserId:
    """Test UserId value object."""
    
    def test_valid_uuid(self):
        """Test valid UUID creation."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        user_id = UserId(uuid_str)
        assert user_id.value == uuid_str
        assert str(user_id) == uuid_str
    
    def test_generate_new_id(self):
        """Test generating new user ID."""
        user_id = UserId.generate()
        assert len(user_id.value) == 36
        assert user_id.value.count("-") == 4
    
    def test_invalid_uuid(self):
        """Test invalid UUID raises ValueError."""
        with pytest.raises(ValueError, match="Invalid user ID format"):
            UserId("not-a-uuid")
    
    def test_empty_id(self):
        """Test empty ID raises ValueError."""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            UserId("")


class TestSessionId:
    """Test SessionId value object."""
    
    def test_valid_uuid(self):
        """Test valid UUID creation."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        session_id = SessionId(uuid_str)
        assert session_id.value == uuid_str
        assert str(session_id) == uuid_str
    
    def test_generate_new_id(self):
        """Test generating new session ID."""
        session_id = SessionId.generate()
        assert len(session_id.value) == 36
        assert session_id.value.count("-") == 4
    
    def test_invalid_uuid(self):
        """Test invalid UUID raises ValueError."""
        with pytest.raises(ValueError, match="Invalid session ID format"):
            SessionId("not-a-uuid")
    
    def test_empty_id(self):
        """Test empty ID raises ValueError."""
        with pytest.raises(ValueError, match="Session ID cannot be empty"):
            SessionId("")


class TestTokenClaims:
    """Test TokenClaims value object."""
    
    def test_create_with_defaults(self):
        """Test creating token claims with default values."""
        claims = TokenClaims(
            user_id="user-123",
            session_id="session-456",
            email="test@example.com"
        )
        assert claims.user_id == "user-123"
        assert claims.session_id == "session-456"
        assert claims.email == "test@example.com"
        assert claims.permissions == []
        assert isinstance(claims.issued_at, datetime)
        assert isinstance(claims.expires_at, datetime)
        assert claims.expires_at > claims.issued_at
    
    def test_create_with_custom_expiration(self):
        """Test creating token claims with custom expiration."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=1)
        
        claims = TokenClaims(
            user_id="user-123",
            session_id="session-456", 
            email="test@example.com",
            issued_at=now,
            expires_at=expires
        )
        assert claims.expires_at == expires
    
    def test_is_expired(self):
        """Test token expiration check."""
        now = datetime.now(timezone.utc)
        past_time = now - timedelta(hours=1)
        
        claims = TokenClaims(
            user_id="user-123",
            session_id="session-456",
            email="test@example.com",
            expires_at=past_time
        )
        assert claims.is_expired() is True
    
    def test_is_not_expired(self):
        """Test token not expired."""
        now = datetime.now(timezone.utc)
        future_time = now + timedelta(hours=1)
        
        claims = TokenClaims(
            user_id="user-123",
            session_id="session-456", 
            email="test@example.com",
            expires_at=future_time
        )
        assert claims.is_expired() is False
    
    def test_to_dict(self):
        """Test converting claims to dictionary."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=15)
        
        claims = TokenClaims(
            user_id="user-123",
            session_id="session-456",
            email="test@example.com",
            permissions=["read", "write"],
            issued_at=now,
            expires_at=expires
        )
        
        data = claims.to_dict()
        assert data["sub"] == "user-123"
        assert data["sid"] == "session-456"
        assert data["email"] == "test@example.com"
        assert data["permissions"] == ["read", "write"]
        assert data["iat"] == int(now.timestamp())
        assert data["exp"] == int(expires.timestamp())
    
    def test_from_dict(self):
        """Test creating claims from dictionary."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=15)
        
        data = {
            "sub": "user-123",
            "sid": "session-456",
            "email": "test@example.com", 
            "permissions": ["read", "write"],
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp())
        }
        
        claims = TokenClaims.from_dict(data)
        assert claims.user_id == "user-123"
        assert claims.session_id == "session-456"
        assert claims.email == "test@example.com"
        assert claims.permissions == ["read", "write"]
        assert abs((claims.issued_at - now).total_seconds()) < 1
        assert abs((claims.expires_at - expires).total_seconds()) < 1


class TestToken:
    """Test Token value object."""
    
    def test_valid_jwt_format(self):
        """Test valid JWT format."""
        token_value = "header.payload.signature"
        token = Token(token_value)
        assert token.value == token_value
        assert "...signature" in str(token)
    
    def test_invalid_jwt_format(self):
        """Test invalid JWT format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid token format"):
            Token("invalid.token")
        
        with pytest.raises(ValueError, match="Invalid token format"):
            Token("too.many.parts.here")
    
    def test_empty_token(self):
        """Test empty token raises ValueError."""
        with pytest.raises(ValueError, match="Token cannot be empty"):
            Token("")
    
    def test_token_with_claims(self):
        """Test token with claims."""
        claims = TokenClaims(
            user_id="user-123",
            session_id="session-456",
            email="test@example.com"
        )
        token = Token("header.payload.signature", claims)
        assert token.claims == claims