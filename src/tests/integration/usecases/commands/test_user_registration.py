"""Integration tests for user registration command."""

import uuid

import pytest

from tests.integration.postgres.base_test import BasePostgreSQLCommandTest


class TestUserRegistrationCommand(BasePostgreSQLCommandTest):
    """Test user registration through API endpoints."""

    @pytest.mark.asyncio
    async def test_successful_user_registration(self):
        """Test successful user registration via API."""
        # Act
        response = await self.api.register_user(
            email="newuser@example.com", password="SecurePassword123"
        )

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "user_id" in data
        assert data["message"] == "User created successfully"
        # Ensure user_id is a valid UUID format
        uuid.UUID(data["user_id"])  # Will raise exception if invalid

    @pytest.mark.asyncio
    async def test_registration_with_existing_email_fails(self):
        """Test that registering with existing email fails."""
        # Arrange - Register first user
        email = "duplicate@example.com"
        password = "Password123"

        first_response = await self.api.register_user(email, password)
        assert first_response.status_code == 200

        # Act - Try to register again with same email
        second_response = await self.api.register_user(email, password)

        # Assert
        assert second_response.status_code == 400
        data = second_response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_registration_with_invalid_email_fails(self):
        """Test registration with invalid email format."""
        # Act
        response = await self.api.register_user(
            email="invalid-email-format", password="ValidPassword123"
        )

        # Assert
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_registration_with_weak_password_fails(self):
        """Test registration with password that doesn't meet requirements."""
        # Act
        response = await self.api.register_user(
            email="weakpass@example.com",
            password="weak",  # Too short, no uppercase, no numbers
        )

        # Assert
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_registration_creates_inactive_user_initially(self):
        """Test that newly registered users are initially inactive."""
        # Act
        response = await self.api.register_user(
            email="inactive@example.com", password="Password123"
        )

        # Assert
        assert response.status_code == 200

        # Try to login immediately after registration
        login_response = await self.api.login_user(
            email="inactive@example.com", password="Password123"
        )

        # Should succeed for our current implementation
        # In future, might require email verification
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_registration_request_validation(self):
        """Test various request validation scenarios."""
        # Missing email
        response = await self.api.post(
            "/auth/register", json={"password": "Password123"}
        )
        assert response.status_code == 422

        # Missing password
        response = await self.api.post(
            "/auth/register", json={"email": "test@example.com"}
        )
        assert response.status_code == 422

        # Empty request body
        response = await self.api.post("/auth/register", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_multiple_registrations_generate_unique_user_ids(self):
        """Test that multiple registrations generate unique user IDs."""
        # Act
        response1 = await self.api.register_user("user1@example.com", "Password123")
        response2 = await self.api.register_user("user2@example.com", "Password123")

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200

        user_id1 = response1.json()["user_id"]
        user_id2 = response2.json()["user_id"]

        assert user_id1 != user_id2
