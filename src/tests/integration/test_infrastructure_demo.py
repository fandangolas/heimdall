"""Demonstration of hybrid test infrastructure benefits."""

import pytest

from heimdall.application.dto import RegisterRequest
from heimdall.domain.value_objects import Email
from tests.integration.test_infrastructure import IntegrationTestBase


class TestInfrastructureIsolation(IntegrationTestBase):
    """Demonstrate test isolation and cleanup with hybrid infrastructure."""

    @pytest.mark.asyncio
    async def test_first_test_creates_state(self):
        """First test creates some state."""
        # Create a user
        user = self.create_test_user("first@example.com", "Password123")

        # Register through the system
        register_request = RegisterRequest(
            email="system@example.com", password="Password123"
        )
        await self.auth_functions["register"](register_request)

        # Verify state exists
        users = self.factory.db.get_users()
        assert len(users) == 2  # Helper user + registered user
        assert "first@example.com" in users
        assert "system@example.com" in users

        # Verify events
        events = self.get_published_events()
        assert len(events) == 1  # UserCreated event

    @pytest.mark.asyncio
    async def test_second_test_has_clean_state(self):
        """Second test should start with clean state (isolation)."""
        # This test should start fresh due to rollback in teardown_method
        users = self.factory.db.get_users()
        assert len(users) == 0  # Clean state

        events = self.get_published_events()
        assert len(events) == 0  # Clean event tracking

        # Create new state for this test
        user = self.create_test_user("second@example.com", "Password456")
        users = self.factory.db.get_users()
        assert len(users) == 1
        assert "second@example.com" in users

    @pytest.mark.asyncio
    async def test_infrastructure_reuse(self):
        """Test that infrastructure is reused but state is isolated."""
        # The factory should be the same instance (shared infrastructure)
        assert hasattr(self.factory, "db")
        assert hasattr(self.factory, "_token_service")

        # But state should be clean for this test
        users = self.factory.db.get_users()
        assert len(users) == 0

        # Token service should work consistently
        user = self.create_test_user("infra@example.com", "Password123")
        session = self.create_test_session(user)

        # Token service behavior should be consistent across tests
        token_service = self.factory._get_token_service()
        token = token_service.generate_token(session)
        assert token.value == "jwt.token.generated"

    def test_transaction_like_behavior(self):
        """Test that the database behaves like transactions."""
        # Direct database manipulation to show transaction behavior
        db = self.factory.db

        # Verify we're in a transaction
        assert db._in_transaction

        # Add something to transaction state
        from heimdall.domain.entities import User
        from heimdall.domain.value_objects import Password

        test_user = User.create(Email("tx@example.com"), Password("Password123"))
        db.get_users()["tx@example.com"] = test_user

        # Should be in transaction state
        assert "tx@example.com" in db._transaction_users

        # But not in main state (until commit)
        assert "tx@example.com" not in db._users

        # Rollback should clear transaction state
        db.rollback_transaction()
        assert "tx@example.com" not in db._transaction_users
        assert len(db._users) == 0

    @pytest.mark.asyncio
    async def test_event_tracking_isolation(self):
        """Test that event tracking is isolated between tests."""
        # Events should start clean
        events = self.get_published_events()
        assert len(events) == 0

        # Register a user to generate events
        register_request = RegisterRequest(
            email="events@example.com", password="Password123"
        )
        await self.auth_functions["register"](register_request)

        # Should have one event
        events = self.get_published_events()
        assert len(events) == 1
        assert events[0].event_type == "UserCreated"  # Domain event

        # Events are tracked per test, isolated from other tests
