"""PostgreSQL integration tests for API endpoints."""

import pytest

from tests.integration.conftest import query_database
from tests.integration.postgres.api_helpers import login_user, register_user


@pytest.mark.asyncio
async def test_user_registration_with_postgres(api_client):
    """Test user registration stores data in PostgreSQL."""
    # Act
    response = await register_user(
        api_client, email="postgres-user@example.com", password="PostgresPassword123"
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "postgres-user@example.com"
    assert "user_id" in data

    # Verify user exists in database
    users = await query_database(
        "SELECT email FROM users WHERE email = $1", "postgres-user@example.com"
    )
    assert len(users) == 1
    assert users[0]["email"] == "postgres-user@example.com"


@pytest.mark.asyncio
async def test_user_login_with_postgres(api_client):
    """Test user login retrieves data from PostgreSQL."""
    # Arrange
    email = "postgres-login@example.com"
    password = "PostgresLogin123"

    register_response = await register_user(api_client, email, password)
    assert register_response.status_code == 200

    # Act
    login_response = await login_user(api_client, email, password)

    # Assert
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
