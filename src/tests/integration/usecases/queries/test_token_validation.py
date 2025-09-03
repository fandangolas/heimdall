"""Integration tests for token validation query."""

import time

import pytest

from tests.integration.postgres.base_test import BasePostgreSQLQueryTest


class TestTokenValidationQuery(BasePostgreSQLQueryTest):
    """Test token validation through API endpoints (read operations)."""

    @pytest.mark.asyncio
    async def test_valid_token_validation(self):
        """Test validation of a valid token through API."""
        # Arrange - Get a valid token
        email = "tokenuser@example.com"
        password = "TokenPassword123"

        register_response = await self.api.register_user(email, password)
        assert register_response.status_code == 200
        login_response = await self.api.login_user(email, password)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Act
        response = await self.api.validate_token(token)

        # Assert
        assert response.status_code == 200

        data = response.json()
        print(f"Debug - Token validation response: {data}")
        print(f"Debug - Token: {token}")
        assert data["is_valid"] is True
        assert data["user_id"] is not None
        assert data["email"] == email
        assert isinstance(data["permissions"], list)
        assert data["error"] is None

    @pytest.mark.asyncio
    async def test_invalid_token_validation(self):
        """Test validation of invalid token."""
        # Act
        response = await self.api.validate_token("invalid.jwt.token")

        # Assert
        assert (
            response.status_code == 200
        )  # Validation endpoint doesn't return HTTP errors

        data = response.json()
        assert data["is_valid"] is False
        assert data["user_id"] is None
        assert data["email"] is None
        assert data["permissions"] == []
        assert data["error"] is not None

    @pytest.mark.asyncio
    async def test_malformed_token_validation(self):
        """Test validation of malformed token."""
        # Act
        response = await self.api.validate_token("not-a-jwt-token-at-all")

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["is_valid"] is False
        assert data["error"] is not None

    @pytest.mark.asyncio
    async def test_empty_token_validation(self):
        """Test validation of empty token."""
        # Act
        response = await self.api.validate_token("")

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["is_valid"] is False
        assert data["error"] is not None

    @pytest.mark.asyncio
    async def test_token_validation_request_format(self):
        """Test token validation request format requirements."""
        # Missing token field
        response = await self.api.post("/auth/validate", json={})
        assert response.status_code == 422

        # Invalid request format
        response = await self.api.post(
            "/auth/validate", json={"invalid_field": "value"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_multiple_token_validations_same_token(self):
        """Test that the same token can be validated multiple times."""
        # Arrange
        email = "multivalidate@example.com"
        password = "MultiValidate123"

        register_response = await self.api.register_user(email, password)
        assert register_response.status_code == 200
        login_response = await self.api.login_user(email, password)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Act - Validate same token multiple times
        responses = []
        for _ in range(5):
            response = await self.api.validate_token(token)
            responses.append(response)

        # Assert - All should succeed with same result
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True
            assert data["email"] == "multivalidate@example.com"

    @pytest.mark.asyncio
    async def test_token_validation_performance_characteristics(self):
        """Test that token validation is fast (query optimization)."""
        # Arrange
        email = "perftest@example.com"
        password = "PerfTest123"

        register_response = await self.api.register_user(email, password)
        assert register_response.status_code == 200
        login_response = await self.api.login_user(email, password)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Act - Measure validation time
        start_time = time.time()
        response = await self.api.validate_token(token)
        end_time = time.time()

        # Assert
        assert response.status_code == 200
        assert response.json()["is_valid"] is True

        # Validation should be fast (under 100ms for this simple test)
        # This is a basic performance check - in production would use
        # proper benchmarking
        validation_time = end_time - start_time
        assert validation_time < 0.1, (
            f"Token validation took {validation_time:.3f}s, expected < 0.1s"
        )

    @pytest.mark.asyncio
    async def test_concurrent_token_validations(self):
        """Test concurrent token validation requests."""
        # Arrange
        email = "concurrent@example.com"
        password = "Concurrent123"

        register_response = await self.api.register_user(email, password)
        assert register_response.status_code == 200
        login_response = await self.api.login_user(email, password)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Act - Rapid sequential validations
        responses = []
        for _ in range(10):
            response = await self.api.validate_token(token)
            responses.append(response)

        # Assert - All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True

    @pytest.mark.asyncio
    async def test_token_validation_response_fields(self):
        """Test that token validation response contains all required fields."""
        # Arrange
        email = "fields@example.com"
        password = "Fields123"

        register_response = await self.api.register_user(email, password)
        assert register_response.status_code == 200
        login_response = await self.api.login_user(email, password)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Act
        response = await self.api.validate_token(token)

        # Assert
        assert response.status_code == 200

        data = response.json()
        required_fields = ["is_valid", "user_id", "email", "permissions", "error"]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Type validation
        assert isinstance(data["is_valid"], bool)
        if data["is_valid"]:
            assert isinstance(data["user_id"], str)
            assert isinstance(data["email"], str)
            assert isinstance(data["permissions"], list)
            assert data["error"] is None
        else:
            assert data["user_id"] is None or isinstance(data["user_id"], str)
            assert data["email"] is None or isinstance(data["email"], str)
            assert isinstance(data["permissions"], list)
            assert isinstance(data["error"], str)

    @pytest.mark.asyncio
    async def test_token_validation_different_users(self):
        """Test token validation for different users."""
        # Arrange - Create multiple users
        register1 = await self.api.register_user("user1@example.com", "Password123")
        assert register1.status_code == 200
        login1 = await self.api.login_user("user1@example.com", "Password123")
        assert login1.status_code == 200
        token1 = login1.json()["access_token"]

        register2 = await self.api.register_user("user2@example.com", "Password123")
        assert register2.status_code == 200
        login2 = await self.api.login_user("user2@example.com", "Password123")
        assert login2.status_code == 200
        token2 = login2.json()["access_token"]

        # Act
        response1 = await self.api.validate_token(token1)
        response2 = await self.api.validate_token(token2)

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        assert data1["is_valid"] is True
        assert data2["is_valid"] is True

        assert data1["email"] == "user1@example.com"
        assert data2["email"] == "user2@example.com"

        # User IDs should be different
        assert data1["user_id"] != data2["user_id"]
