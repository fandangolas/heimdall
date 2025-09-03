"""Integration tests for token validation query."""

import time

import pytest

from tests.integration.postgres.api_helpers import (
    get_current_user,
    login_user,
    register_user,
    validate_token,
)


@pytest.mark.asyncio
async def test_valid_token_validation(api_client):
    """Test validation of a valid token through API."""
    # Arrange - Get a valid token
    email = "tokenuser@example.com"
    password = "TokenPassword123"

    register_response = await register_user(api_client, email, password)
    assert register_response.status_code == 200
    login_response = await login_user(api_client, email, password)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Act
    response = await validate_token(api_client, token)

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
async def test_invalid_token_validation(api_client):
    """Test validation of invalid token."""
    # Act
    response = await validate_token(api_client, "invalid.jwt.token")

    # Assert
    assert response.status_code == 200  # Validation endpoint doesn't return HTTP errors

    data = response.json()
    assert data["is_valid"] is False
    assert data["user_id"] is None
    assert data["email"] is None
    assert data["permissions"] == []
    assert data["error"] is not None


@pytest.mark.asyncio
async def test_malformed_token_validation(api_client):
    """Test validation of malformed tokens."""
    malformed_tokens = [
        "not-a-jwt",
        "a.b",  # Missing third part
        "a.b.c.d",  # Too many parts
        "",  # Empty
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",  # Only header
    ]

    for token in malformed_tokens:
        response = await validate_token(api_client, token)
        assert response.status_code == 200

        data = response.json()
        assert data["is_valid"] is False, f"Token should be invalid: {token}"
        assert data["error"] is not None


@pytest.mark.asyncio
async def test_expired_token_validation(api_client):
    """Test validation of expired token."""
    # This is a known expired token for testing
    # In real tests, you'd generate one with a past expiry
    expired_token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIiwiZXhwIjoxMDAwMDAwMDAwfQ."
        "signature_doesnt_matter_for_test"
    )

    response = await validate_token(api_client, expired_token)
    assert response.status_code == 200

    data = response.json()
    assert data["is_valid"] is False
    assert "expir" in data["error"].lower() or "invalid" in data["error"].lower()


@pytest.mark.asyncio
async def test_token_validation_performance(api_client):
    """Test token validation query performance (read-heavy operation)."""
    # Arrange - Get a valid token
    await register_user(
        api_client, email="perfuser@example.com", password="PerfPassword123"
    )
    login_response = await login_user(
        api_client, email="perfuser@example.com", password="PerfPassword123"
    )
    token = login_response.json()["access_token"]

    # Act - Validate token multiple times
    start_time = time.time()
    num_validations = 20

    for _ in range(num_validations):
        response = await validate_token(api_client, token)
        assert response.status_code == 200
        assert response.json()["is_valid"] is True

    elapsed_time = time.time() - start_time
    avg_time = elapsed_time / num_validations

    # Assert - Should be fast (this is the 99% use case)
    assert avg_time < 0.1, f"Token validation too slow: {avg_time:.3f}s avg"


@pytest.mark.asyncio
async def test_get_current_user_with_valid_token(api_client):
    """Test getting current user with valid token."""
    # Arrange
    email = "currentuser@example.com"
    password = "CurrentPassword123"

    await register_user(api_client, email, password)
    login_response = await login_user(api_client, email, password)
    token = login_response.json()["access_token"]

    # Act
    response = await get_current_user(api_client, token)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "user_id" in data


@pytest.mark.asyncio
async def test_get_current_user_with_invalid_token(api_client):
    """Test getting current user with invalid token."""
    # Act
    response = await get_current_user(api_client, "invalid.token.here")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_multiple_token_validations_same_token(api_client):
    """Test that the same token can be validated multiple times."""
    # Arrange
    email = "multivalidate@example.com"
    password = "MultiValidate123"

    await register_user(api_client, email, password)
    login_response = await login_user(api_client, email, password)
    token = login_response.json()["access_token"]

    # Act - Validate same token multiple times
    results = []
    for _ in range(5):
        response = await validate_token(api_client, token)
        results.append(response)

    # Assert - All validations should succeed
    for response in results:
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["email"] == email
