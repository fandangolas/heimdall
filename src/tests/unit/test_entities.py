"""Tests for domain entities."""

from datetime import UTC, datetime, timedelta

import pytest

from heimdall.domain.entities import Session, User
from heimdall.domain.value_objects import (
    Email,
    Password,
    PasswordHash,
    SessionId,
    UserId,
)


class TestUser:
    """Test User entity."""

    def test_create_user(self):
        """Test creating a new user."""
        email = Email("test@example.com")
        password = Password("ValidPass123")

        user = User.create(email, password)

        assert isinstance(user.id, UserId)
        assert user.email == email
        assert isinstance(user.password_hash, PasswordHash)
        assert user.is_active is True
        assert user.is_verified is False
        assert user.permissions == []
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        assert user.last_login_at is None

    def test_authenticate_success(self):
        """Test successful authentication."""
        email = Email("test@example.com")
        password = Password("ValidPass123")
        user = User.create(email, password)

        session = user.authenticate(password)

        assert isinstance(session, Session)
        assert session.user_id == user.id
        assert session.email == user.email
        assert session.permissions == user.permissions
        assert user.last_login_at is not None

    def test_authenticate_wrong_password(self):
        """Test authentication with wrong password."""
        email = Email("test@example.com")
        password = Password("ValidPass123")
        wrong_password = Password("WrongPass456")
        user = User.create(email, password)

        with pytest.raises(ValueError, match="Invalid credentials"):
            user.authenticate(wrong_password)

    def test_authenticate_inactive_user(self):
        """Test authentication with inactive user."""
        email = Email("test@example.com")
        password = Password("ValidPass123")
        user = User.create(email, password)
        user.deactivate()

        with pytest.raises(ValueError, match="User account is inactive"):
            user.authenticate(password)

    def test_change_password_success(self):
        """Test successful password change."""
        email = Email("test@example.com")
        current_password = Password("CurrentPass123")
        new_password = Password("NewPass456")
        user = User.create(email, current_password)
        old_updated_at = user.updated_at

        user.change_password(current_password, new_password)

        assert user.password_hash.verify(new_password) is True
        assert user.password_hash.verify(current_password) is False
        assert user.updated_at > old_updated_at

    def test_change_password_wrong_current(self):
        """Test password change with wrong current password."""
        email = Email("test@example.com")
        current_password = Password("CurrentPass123")
        wrong_password = Password("WrongPass456")
        new_password = Password("NewPass789")
        user = User.create(email, current_password)

        with pytest.raises(ValueError, match="Current password is incorrect"):
            user.change_password(wrong_password, new_password)

    def test_grant_permission(self):
        """Test granting permission to user."""
        user = User.create(Email("test@example.com"), Password("ValidPass123"))
        old_updated_at = user.updated_at

        user.grant_permission("read")

        assert "read" in user.permissions
        assert user.updated_at > old_updated_at

    def test_grant_duplicate_permission(self):
        """Test granting duplicate permission doesn't add twice."""
        user = User.create(Email("test@example.com"), Password("ValidPass123"))

        user.grant_permission("read")
        user.grant_permission("read")

        assert user.permissions.count("read") == 1

    def test_revoke_permission(self):
        """Test revoking permission from user."""
        user = User.create(Email("test@example.com"), Password("ValidPass123"))
        user.grant_permission("read")
        user.grant_permission("write")
        old_updated_at = user.updated_at

        user.revoke_permission("read")

        assert "read" not in user.permissions
        assert "write" in user.permissions
        assert user.updated_at > old_updated_at

    def test_revoke_nonexistent_permission(self):
        """Test revoking permission that user doesn't have."""
        user = User.create(Email("test@example.com"), Password("ValidPass123"))
        old_permissions = user.permissions.copy()

        user.revoke_permission("nonexistent")

        assert user.permissions == old_permissions

    def test_deactivate_user(self):
        """Test deactivating user."""
        user = User.create(Email("test@example.com"), Password("ValidPass123"))
        old_updated_at = user.updated_at

        user.deactivate()

        assert user.is_active is False
        assert user.updated_at > old_updated_at

    def test_activate_user(self):
        """Test activating user."""
        user = User.create(Email("test@example.com"), Password("ValidPass123"))
        user.deactivate()
        old_updated_at = user.updated_at

        user.activate()

        assert user.is_active is True
        assert user.updated_at > old_updated_at

    def test_verify_user(self):
        """Test verifying user."""
        user = User.create(Email("test@example.com"), Password("ValidPass123"))
        old_updated_at = user.updated_at

        user.verify()

        assert user.is_verified is True
        assert user.updated_at > old_updated_at


class TestSession:
    """Test Session entity."""

    def test_create_for_user(self):
        """Test creating session for user."""
        user_id = UserId.generate()
        email = Email("test@example.com")
        permissions = ["read", "write"]

        session = Session.create_for_user(user_id, email, permissions)

        assert isinstance(session.id, SessionId)
        assert session.user_id == user_id
        assert session.email == email
        assert session.permissions == permissions
        assert session.permissions is not permissions  # Should be a copy
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.expires_at, datetime)
        assert session.expires_at > session.created_at
        assert session.is_active is True

    def test_is_valid_active_session(self):
        """Test valid active session."""
        user_id = UserId.generate()
        email = Email("test@example.com")
        session = Session.create_for_user(user_id, email, [])

        assert session.is_valid() is True
        assert session.is_expired() is False

    def test_is_valid_expired_session(self):
        """Test expired session is not valid."""
        user_id = UserId.generate()
        email = Email("test@example.com")
        session = Session.create_for_user(user_id, email, [])

        # Manually set expiration to past
        session.expires_at = datetime.now(UTC) - timedelta(hours=1)

        assert session.is_valid() is False
        assert session.is_expired() is True

    def test_is_valid_inactive_session(self):
        """Test inactive session is not valid."""
        user_id = UserId.generate()
        email = Email("test@example.com")
        session = Session.create_for_user(user_id, email, [])

        session.invalidate()

        assert session.is_valid() is False
        assert session.is_active is False

    def test_invalidate_session(self):
        """Test invalidating session."""
        user_id = UserId.generate()
        email = Email("test@example.com")
        session = Session.create_for_user(user_id, email, [])

        session.invalidate()

        assert session.is_active is False

    def test_to_token_claims(self):
        """Test converting session to token claims."""
        user_id = UserId.generate()
        email = Email("test@example.com")
        permissions = ["read", "write"]
        session = Session.create_for_user(user_id, email, permissions)

        claims = session.to_token_claims()

        assert claims.user_id == str(user_id)
        assert claims.session_id == str(session.id)
        assert claims.email == str(email)
        assert claims.permissions == permissions
        assert claims.permissions is not permissions  # Should be a copy

    def test_session_with_custom_expiration(self):
        """Test session with custom expiration time."""
        user_id = UserId.generate()
        email = Email("test@example.com")
        custom_expiration = datetime.now(UTC) + timedelta(hours=2)

        session = Session(
            id=SessionId.generate(),
            user_id=user_id,
            email=email,
            permissions=[],
            expires_at=custom_expiration,
        )

        assert session.expires_at == custom_expiration
