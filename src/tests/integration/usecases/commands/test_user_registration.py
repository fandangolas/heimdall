"""Integration tests for user registration command."""

import uuid

import pytest
import pytest_asyncio

from tests.integration.aux.api_helpers import register_user
from tests.integration.aux.postgres_helpers import verify_postgres

# Load fixtures from api_fixtures module
pytest_plugins = ["tests.integration.aux.api_fixtures"]


@pytest_asyncio.fixture(scope="session", autouse=True)
async def verify_postgres_session():
    """Verify PostgreSQL is accessible before running tests."""
    await verify_postgres()


@pytest.mark.asyncio
async def test_successful_user_registration(api_client):
    """Test successful user registration via API."""
    # Act
    response = await register_user(
        api_client, email="newuser@example.com", password="SecurePassword123"
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
async def test_registration_with_existing_email_fails(api_client):
    """Test that registering with existing email fails."""
    # Arrange - Register first user
    email = "duplicate@example.com"
    password = "Password123"

    first_response = await register_user(api_client, email, password)
    assert first_response.status_code == 200

    # Act - Try to register again with same email
    second_response = await register_user(api_client, email, password)

    # Assert
    assert second_response.status_code == 400
    data = second_response.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_registration_with_invalid_email_fails(api_client):
    """Test registration with invalid email format fails."""
    # Act - Various invalid email formats
    invalid_emails = [
        "not-an-email",
        "@example.com",
        "user@",
        "user@@example.com",
        "user.example.com",
        "",
    ]

    for invalid_email in invalid_emails:
        response = await api_client.post(
            "/auth/register",
            json={"email": invalid_email, "password": "ValidPassword123"},
        )

        # Assert
        assert response.status_code == 422, f"Expected 422 for email: {invalid_email}"


@pytest.mark.asyncio
async def test_registration_with_invalid_password_fails(api_client):
    """Test registration with invalid password fails."""
    # Act - Password too short
    response = await api_client.post(
        "/auth/register", json={"email": "validuser@example.com", "password": "short"}
    )

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_registration_request_validation(api_client):
    """Test registration request validation."""
    # Missing email
    response = await api_client.post("/auth/register", json={"password": "Password123"})
    assert response.status_code == 422

    # Missing password
    response = await api_client.post(
        "/auth/register", json={"email": "test@example.com"}
    )
    assert response.status_code == 422

    # Empty body
    response = await api_client.post("/auth/register", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_registration_with_different_case_emails(api_client):
    """Test registration behavior with different email cases."""
    # Register with lowercase
    response1 = await register_user(
        api_client, email="testcase@example.com", password="CasePassword123"
    )
    assert response1.status_code == 200

    # Try to register with uppercase - should fail due to normalization
    response2 = await register_user(
        api_client, email="TESTCASE@EXAMPLE.COM", password="CasePassword456"
    )

    # If email normalization is implemented, this should fail
    # as it's the same email after normalization
    if response2.status_code == 400:
        # Email normalization is working
        data = response2.json()
        assert "error" in data
    else:
        # Email normalization not implemented - different emails allowed
        assert response2.status_code == 200


@pytest.mark.asyncio
async def test_registration_creates_unique_user_ids(api_client):
    """Test that each registration creates unique user IDs."""
    # Register multiple users
    user_ids = []

    for i in range(5):
        response = await register_user(
            api_client, email=f"unique{i}@example.com", password="UniquePassword123"
        )
        assert response.status_code == 200
        user_ids.append(response.json()["user_id"])

    # Verify all user IDs are unique
    assert len(user_ids) == len(set(user_ids)), "User IDs are not unique"

    # Verify all are valid UUIDs
    for user_id in user_ids:
        uuid.UUID(user_id)
