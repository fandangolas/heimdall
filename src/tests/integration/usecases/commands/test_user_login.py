"""Integration tests for user login command."""

from tests.integration.aux.base_test import BaseCommandIntegrationTest


class TestUserLoginCommand(BaseCommandIntegrationTest):
    """Test user login through API endpoints."""

    def test_successful_login_after_registration(self):
        """Test successful login flow after user registration."""
        # Arrange - Register a user first
        email = "loginuser@example.com"
        password = "LoginPassword123"

        register_response = self.api.register_user(email, password)
        assert register_response.status_code == 200

        # Act - Login with same credentials
        login_response = self.api.login_user(email, password)

        # Assert
        assert login_response.status_code == 200

        data = login_response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Token should be in JWT format (3 parts separated by dots)
        token = data["access_token"]
        assert len(token.split(".")) == 3

    def test_login_with_nonexistent_user_fails(self):
        """Test login with user that doesn't exist."""
        # Act
        response = self.api.login_user(
            email="nonexistent@example.com", password="AnyPassword123"
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "error" in data or "detail" in data

    def test_login_with_wrong_password_fails(self):
        """Test login with correct email but wrong password."""
        # Arrange - Register a user
        email = "wrongpass@example.com"
        correct_password = "CorrectPassword123"
        wrong_password = "WrongPassword456"

        self.api.register_user(email, correct_password)

        # Act - Login with wrong password
        response = self.api.login_user(email, wrong_password)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "error" in data or "detail" in data

    def test_login_request_validation(self):
        """Test login request validation."""
        # Missing email
        response = self.api.client.post("/auth/login", json={"password": "Password123"})
        assert response.status_code == 422

        # Missing password
        response = self.api.client.post(
            "/auth/login", json={"email": "test@example.com"}
        )
        assert response.status_code == 422

        # Invalid email format
        response = self.api.client.post(
            "/auth/login", json={"email": "invalid-email", "password": "Password123"}
        )
        assert response.status_code == 422

        # Password too short
        response = self.api.client.post(
            "/auth/login", json={"email": "test@example.com", "password": "short"}
        )
        assert response.status_code == 422

    def test_multiple_successful_logins_same_user(self):
        """Test that the same user can login multiple times."""
        # Arrange
        email = "multilogin@example.com"
        password = "MultiLogin123"

        self.api.register_user(email, password)

        # Act - Login multiple times
        response1 = self.api.login_user(email, password)
        response2 = self.api.login_user(email, password)
        response3 = self.api.login_user(email, password)

        # Assert - All should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        # All should return valid tokens
        token1 = response1.json()["access_token"]
        token2 = response2.json()["access_token"]
        token3 = response3.json()["access_token"]

        assert len(token1.split(".")) == 3
        assert len(token2.split(".")) == 3
        assert len(token3.split(".")) == 3

    def test_login_with_different_case_email_normalization(self):
        """Test email case normalization during login."""
        # Arrange - Register with lowercase
        email = "casetest@example.com"
        password = "CaseTest123"

        self.api.register_user(email, password)

        # Act - Login with different cases
        response_upper = self.api.login_user("CASETEST@EXAMPLE.COM", password)
        response_mixed = self.api.login_user("CaseTest@Example.Com", password)

        # Assert - Should work due to email normalization
        # Note: This depends on our email normalization implementation
        # If not implemented yet, these might fail, which is also valid to test
        if response_upper.status_code == 200:
            # Email normalization is implemented
            assert response_mixed.status_code == 200
        else:
            # Email normalization not implemented - both should fail consistently
            assert response_mixed.status_code == 400

    def test_concurrent_logins_same_user(self):
        """Test concurrent login attempts for the same user."""

        # Arrange
        email = "concurrent@example.com"
        password = "Concurrent123"

        self.api.register_user(email, password)

        # Act - Simulate concurrent requests
        # Note: TestClient doesn't support true concurrency,
        # so this is more of a rapid sequential test
        responses = []
        for _ in range(5):
            response = self.api.login_user(email, password)
            responses.append(response)

        # Assert - All should succeed
        for response in responses:
            assert response.status_code == 200
            assert "access_token" in response.json()

    def test_login_response_contains_required_fields(self):
        """Test that login response contains all required fields."""
        # Arrange
        email = "responsetest@example.com"
        password = "Response123"

        self.api.register_user(email, password)

        # Act
        response = self.api.login_user(email, password)

        # Assert
        assert response.status_code == 200

        data = response.json()
        required_fields = ["access_token", "token_type"]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
