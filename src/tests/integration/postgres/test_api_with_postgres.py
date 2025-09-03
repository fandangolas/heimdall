"""PostgreSQL integration tests for API endpoints."""

import pytest

from tests.integration.postgres.base_test import BasePostgreSQLCommandTest


class TestAPIWithPostgreSQL(BasePostgreSQLCommandTest):
    """Test API endpoints with PostgreSQL backend."""

    @pytest.mark.asyncio
    async def test_user_registration_with_postgres(self):
        """Test user registration stores data in PostgreSQL."""
        # Act
        response = await self.api.register_user(
            email="postgres-user@example.com", password="PostgresPassword123"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "postgres-user@example.com"
        assert "user_id" in data

        # Verify user exists in database
        user_from_db = await self.api.get_user_from_db("postgres-user@example.com")
        assert user_from_db is not None
        assert user_from_db["email"] == "postgres-user@example.com"

    @pytest.mark.asyncio
    async def test_user_login_with_postgres(self):
        """Test user login retrieves data from PostgreSQL."""
        # Arrange
        email = "postgres-login@example.com"
        password = "PostgresLogin123"

        register_response = await self.api.register_user(email, password)
        assert register_response.status_code == 200

        # Act
        login_response = await self.api.login_user(email, password)

        # Assert
        assert login_response.status_code == 200
        data = login_response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
