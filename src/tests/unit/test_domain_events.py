"""Tests for domain events."""

from datetime import UTC, datetime

from heimdall.domain.events import (
    DomainEvent,
    UserActivated,
    UserCreated,
    UserDeactivated,
    UserLoggedIn,
    UserLoggedOut,
    UserPasswordChanged,
    UserPermissionGranted,
    UserPermissionRevoked,
)
from heimdall.domain.value_objects import Email, SessionId, UserId


class TestDomainEvent:
    """Test base DomainEvent class."""

    def test_create_domain_event(self):
        """Test creating a domain event."""
        event = DomainEvent()

        assert event.event_id is not None
        assert len(event.event_id) == 36  # UUID format
        assert isinstance(event.occurred_at, datetime)
        assert event.occurred_at.tzinfo == UTC
        assert event.event_type == "DomainEvent"

    def test_to_dict(self):
        """Test converting event to dictionary."""
        event = DomainEvent()

        data = event.to_dict()

        assert "event_id" in data
        assert "event_type" in data
        assert "occurred_at" in data
        assert "data" in data
        assert data["event_type"] == "DomainEvent"
        assert isinstance(data["occurred_at"], str)


class TestUserEvents:
    """Test user-related domain events."""

    def test_user_created_event(self):
        """Test UserCreated event."""
        user_id = UserId.generate()
        email = Email("test@example.com")

        event = UserCreated(user_id=user_id, email=email)

        assert event.user_id == user_id
        assert event.email == email
        assert event.event_type == "UserCreated"
        assert isinstance(event.occurred_at, datetime)

        data = event.to_dict()
        assert data["event_type"] == "UserCreated"
        assert str(user_id) in data["data"]["user_id"]
        assert str(email) in data["data"]["email"]

    def test_user_logged_in_event(self):
        """Test UserLoggedIn event."""
        user_id = UserId.generate()
        session_id = SessionId.generate()
        email = Email("test@example.com")

        event = UserLoggedIn(user_id=user_id, session_id=session_id, email=email)

        assert event.user_id == user_id
        assert event.session_id == session_id
        assert event.email == email
        assert event.event_type == "UserLoggedIn"

        data = event.to_dict()
        assert data["event_type"] == "UserLoggedIn"
        assert str(user_id) in data["data"]["user_id"]
        assert str(session_id) in data["data"]["session_id"]
        assert str(email) in data["data"]["email"]

    def test_user_logged_out_event(self):
        """Test UserLoggedOut event."""
        user_id = UserId.generate()
        session_id = SessionId.generate()

        event = UserLoggedOut(user_id=user_id, session_id=session_id)

        assert event.user_id == user_id
        assert event.session_id == session_id
        assert event.event_type == "UserLoggedOut"

    def test_user_password_changed_event(self):
        """Test UserPasswordChanged event."""
        user_id = UserId.generate()

        event = UserPasswordChanged(user_id=user_id)

        assert event.user_id == user_id
        assert event.event_type == "UserPasswordChanged"

    def test_user_permission_granted_event(self):
        """Test UserPermissionGranted event."""
        user_id = UserId.generate()
        permission = "read"

        event = UserPermissionGranted(user_id=user_id, permission=permission)

        assert event.user_id == user_id
        assert event.permission == permission
        assert event.event_type == "UserPermissionGranted"

        data = event.to_dict()
        assert data["data"]["permission"] == permission

    def test_user_permission_revoked_event(self):
        """Test UserPermissionRevoked event."""
        user_id = UserId.generate()
        permission = "write"

        event = UserPermissionRevoked(user_id=user_id, permission=permission)

        assert event.user_id == user_id
        assert event.permission == permission
        assert event.event_type == "UserPermissionRevoked"

    def test_user_deactivated_event(self):
        """Test UserDeactivated event."""
        user_id = UserId.generate()
        reason = "Account suspended"

        event = UserDeactivated(user_id=user_id, reason=reason)

        assert event.user_id == user_id
        assert event.reason == reason
        assert event.event_type == "UserDeactivated"

        data = event.to_dict()
        assert data["data"]["reason"] == reason

    def test_user_deactivated_event_no_reason(self):
        """Test UserDeactivated event without reason."""
        user_id = UserId.generate()

        event = UserDeactivated(user_id=user_id)

        assert event.user_id == user_id
        assert event.reason is None
        assert event.event_type == "UserDeactivated"

    def test_user_activated_event(self):
        """Test UserActivated event."""
        user_id = UserId.generate()

        event = UserActivated(user_id=user_id)

        assert event.user_id == user_id
        assert event.event_type == "UserActivated"

    def test_event_serialization(self):
        """Test event serialization to dict."""
        user_id = UserId.generate()
        email = Email("test@example.com")
        event = UserCreated(user_id=user_id, email=email)

        data = event.to_dict()

        # Ensure all required fields are present
        assert "event_id" in data
        assert "event_type" in data
        assert "occurred_at" in data
        assert "data" in data

        # Ensure data contains event-specific fields
        assert "user_id" in data["data"]
        assert "email" in data["data"]

        # Ensure datetime is serialized as ISO string
        assert isinstance(data["occurred_at"], str)
        datetime.fromisoformat(
            data["occurred_at"].replace("Z", "+00:00")
        )  # Should not raise

    def test_multiple_events_have_different_ids(self):
        """Test that multiple events have different IDs."""
        user_id = UserId.generate()

        event1 = UserPasswordChanged(user_id=user_id)
        event2 = UserPasswordChanged(user_id=user_id)

        assert event1.event_id != event2.event_id
        assert (
            event1.occurred_at <= event2.occurred_at
        )  # Second event should be later or same time
