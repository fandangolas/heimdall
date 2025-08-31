"""Integration tests for CQRS command/query interaction using hybrid infrastructure."""

import pytest

from heimdall.application.dto import LoginRequest, RegisterRequest
from heimdall.domain.value_objects import Token
from tests.integration.aux.test_infrastructure import IntegrationTestBase


class TestCQRSIntegration(IntegrationTestBase):
    """Integration tests demonstrating CQRS command/query flow."""

    @pytest.mark.asyncio
    async def test_login_command_creates_session_for_query_validation(self):
        """Test that login command creates session that can be validated by query."""
        # Arrange - Create test user using helper
        user = self.create_test_user("test@example.com", "Password123")
        _session = self.create_test_session(user)  # Setup for testing

        # Act 1: Login (command) - creates session
        login_request = LoginRequest(email="test@example.com", password="Password123")
        login_response = await self.auth_functions["login"](login_request)

        # Act 2: Validate token (query) - uses session created by command
        token = Token("jwt.token.generated")
        validate_result = await self.auth_functions["validate"](token)

        # Assert: End-to-end flow works
        assert login_response.access_token == "jwt.token.generated"
        assert validate_result.is_valid is True
        assert validate_result.user_id == str(user.id)
        assert validate_result.email == str(user.email)

        # Verify events were published
        events = self.get_published_events()
        assert len(events) == 1  # UserLoggedIn event

        # Verify session was stored and retrieved
        sessions = self.factory.db.get_sessions()
        assert len(sessions) == 1

    @pytest.mark.asyncio
    async def test_register_then_login_cqrs_flow(self):
        """Test full registration -> login -> validation CQRS flow."""
        # Act 1: Register user
        register_request = RegisterRequest(
            email="new@example.com", password="Password123"
        )
        register_response = await self.auth_functions["register"](register_request)

        # Act 2: Setup login for registered user
        user = self.factory.db.get_users()["new@example.com"]
        _session = self.create_test_session(user)  # Setup for testing

        login_request = LoginRequest(email="new@example.com", password="Password123")
        login_response = await self.auth_functions["login"](login_request)

        # Act 3: Validate token
        token = Token("jwt.token.generated")
        validate_result = await self.auth_functions["validate"](token)

        # Assert: Full CQRS flow works
        assert register_response.email == "new@example.com"
        assert register_response.user_id == str(user.id)
        assert login_response.access_token == "jwt.token.generated"
        assert validate_result.is_valid is True
        assert validate_result.user_id == register_response.user_id

        # Verify complete workflow
        events = self.get_published_events()
        assert len(events) == 2  # UserCreated + UserLoggedIn events

        # Verify state consistency across CQRS sides
        users = self.factory.db.get_users()
        sessions = self.factory.db.get_sessions()
        assert len(users) == 1
        assert len(sessions) == 1
        assert "new@example.com" in users

    @pytest.mark.asyncio
    async def test_parallel_operations_with_isolated_state(self):
        """Test that multiple operations can run with proper state isolation."""
        # Arrange - Create two users
        user1 = self.create_test_user("user1@example.com", "Password123")
        user2 = self.create_test_user("user2@example.com", "Password456")

        _session1 = self.create_test_session(user1)  # Setup for testing
        _session2 = self.create_test_session(user2)  # Setup for testing

        # Act - Concurrent logins
        import asyncio

        login1 = LoginRequest(email="user1@example.com", password="Password123")
        login2 = LoginRequest(email="user2@example.com", password="Password456")

        response1, response2 = await asyncio.gather(
            self.auth_functions["login"](login1), self.auth_functions["login"](login2)
        )

        # Assert - Both operations succeeded independently
        assert response1.access_token == "jwt.token.generated"
        assert response2.access_token == "jwt.token.generated"

        # Verify both users and sessions are tracked
        users = self.factory.db.get_users()
        sessions = self.factory.db.get_sessions()

        assert len(users) == 2
        assert len(sessions) == 2
        assert "user1@example.com" in users
        assert "user2@example.com" in users

        # Verify events for both operations
        events = self.get_published_events()
        assert len(events) == 2  # Two UserLoggedIn events
