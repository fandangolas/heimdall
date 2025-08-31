"""Integration tests for token validation query."""

from tests.integration.aux.base_test import BaseQueryIntegrationTest


class TestTokenValidationQuery(BaseQueryIntegrationTest):
    """Test token validation through API endpoints (read operations)."""

    def test_valid_token_validation(self):
        """Test validation of a valid token through API."""
        # Arrange - Get a valid token
        email = "tokenuser@example.com"
        password = "TokenPassword123"
        token = self.api.register_and_login(email, password)

        # Act
        response = self.api.validate_token(token)

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["is_valid"] is True
        assert data["user_id"] is not None
        assert data["email"] == email
        assert isinstance(data["permissions"], list)
        assert data["error"] is None

    def test_invalid_token_validation(self):
        """Test validation of invalid token."""
        # Act
        response = self.api.validate_token("invalid.jwt.token")

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

    def test_malformed_token_validation(self):
        """Test validation of malformed token."""
        # Act
        response = self.api.validate_token("not-a-jwt-token-at-all")

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["is_valid"] is False
        assert data["error"] is not None

    def test_empty_token_validation(self):
        """Test validation of empty token."""
        # Act
        response = self.api.validate_token("")

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["is_valid"] is False
        assert data["error"] is not None

    def test_token_validation_request_format(self):
        """Test token validation request format requirements."""
        # Missing token field
        response = self.api.client.post("/auth/validate", json={})
        assert response.status_code == 422

        # Invalid request format
        response = self.api.client.post(
            "/auth/validate", json={"invalid_field": "value"}
        )
        assert response.status_code == 422

    def test_multiple_token_validations_same_token(self):
        """Test that the same token can be validated multiple times."""
        # Arrange
        token = self.api.register_and_login(
            "multivalidate@example.com", "MultiValidate123"
        )

        # Act - Validate same token multiple times
        responses = []
        for _ in range(5):
            response = self.api.validate_token(token)
            responses.append(response)

        # Assert - All should succeed with same result
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True
            assert data["email"] == "multivalidate@example.com"

    def test_token_validation_performance_characteristics(self):
        """Test that token validation is fast (query optimization)."""
        import time

        # Arrange
        token = self.api.register_and_login("perftest@example.com", "PerfTest123")

        # Act - Measure validation time
        start_time = time.time()
        response = self.api.validate_token(token)
        end_time = time.time()

        # Assert
        assert response.status_code == 200
        assert response.json()["is_valid"] is True

        # Validation should be fast (under 100ms for this simple test)
        # This is a basic performance check - in production would use
        # proper benchmarking
        validation_time = end_time - start_time
        assert (
            validation_time < 0.1
        ), f"Token validation took {validation_time:.3f}s, expected < 0.1s"

    def test_concurrent_token_validations(self):
        """Test concurrent token validation requests."""
        # Arrange
        token = self.api.register_and_login("concurrent@example.com", "Concurrent123")

        # Act - Rapid sequential validations (simulating concurrency)
        responses = []
        for _ in range(10):
            response = self.api.validate_token(token)
            responses.append(response)

        # Assert - All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True

    def test_token_validation_response_fields(self):
        """Test that token validation response contains all required fields."""
        # Arrange
        token = self.api.register_and_login("fields@example.com", "Fields123")

        # Act
        response = self.api.validate_token(token)

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

    def test_token_validation_different_users(self):
        """Test token validation for different users."""
        # Arrange - Create multiple users
        token1 = self.api.register_and_login("user1@example.com", "Password123")
        token2 = self.api.register_and_login("user2@example.com", "Password123")

        # Act
        response1 = self.api.validate_token(token1)
        response2 = self.api.validate_token(token2)

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
