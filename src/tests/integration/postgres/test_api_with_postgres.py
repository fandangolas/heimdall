"""Integration tests using PostgreSQL with FastAPI."""

import asyncio
import os

import asyncpg
import pytest
from fastapi.testclient import TestClient

from heimdall.presentation.api.main import create_app


@pytest.fixture(scope="module")
def postgres_app():
    """Create FastAPI app configured for PostgreSQL."""
    # Set environment for PostgreSQL
    os.environ["PERSISTENCE_MODE"] = "postgres"
    app = create_app()
    return app


@pytest.fixture(scope="module")
def postgres_client(postgres_app):
    """Create test client for PostgreSQL-enabled app."""

    # Manually initialize database before creating client
    async def init_db():
        from heimdall.infrastructure.persistence.postgres.database import (
            initialize_database,
        )

        await initialize_database()

    asyncio.run(init_db())
    return TestClient(postgres_app)


@pytest.fixture(autouse=True)
def clean_database_simple():
    """Simple database cleanup using direct connection."""

    async def clean_tables():
        conn = await asyncpg.connect(
            "postgresql://heimdall_user:heimdall_secure_password@localhost:5432/heimdall"
        )
        try:
            # Clean up tables in correct order (respecting foreign keys)
            await conn.execute("TRUNCATE TABLE audit_events CASCADE;")
            await conn.execute("TRUNCATE TABLE password_reset_tokens CASCADE;")
            await conn.execute("TRUNCATE TABLE user_permissions CASCADE;")
            await conn.execute("TRUNCATE TABLE user_roles CASCADE;")
            await conn.execute("TRUNCATE TABLE role_permissions CASCADE;")
            await conn.execute("TRUNCATE TABLE sessions CASCADE;")
            await conn.execute("TRUNCATE TABLE users CASCADE;")
            await conn.execute("TRUNCATE TABLE permissions CASCADE;")
            await conn.execute("TRUNCATE TABLE roles CASCADE;")
        except Exception as e:
            print(f"Warning during cleanup: {e}")
        finally:
            await conn.close()

    # Clean before test
    asyncio.run(clean_tables())
    yield
    # Clean after test
    asyncio.run(clean_tables())


def test_user_registration_with_postgres(postgres_client):
    """Test user registration stores data in PostgreSQL."""
    # Register user via API
    response = postgres_client.post(
        "/auth/register",
        json={"email": "postgres_test@example.com", "password": "SecurePass123"},
    )

    # Debug: print response details if not 200
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        print(f"Response JSON: {response.json()}")

    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert data["email"] == "postgres_test@example.com"

    # Verify user exists in database directly
    async def verify_user_exists():
        conn = await asyncpg.connect(
            "postgresql://heimdall_user:heimdall_secure_password@localhost:5432/heimdall"
        )
        try:
            user = await conn.fetchrow(
                "SELECT id, email, status, is_verified FROM users WHERE email = $1",
                "postgres_test@example.com",
            )
            assert user is not None
            assert user["email"] == "postgres_test@example.com"
            assert user["status"] == "inactive"  # Should be inactive initially
            assert user["is_verified"] is False
            return user
        finally:
            await conn.close()

    user = asyncio.run(verify_user_exists())
    assert str(user["id"]) == data["user_id"]


def test_user_login_with_postgres(postgres_client):
    """Test user login flow with PostgreSQL persistence."""
    email = "login_test@example.com"
    password = "SecurePass123"

    # First create and activate a user directly in database
    async def create_active_user():
        conn = await asyncpg.connect(
            "postgresql://heimdall_user:heimdall_secure_password@localhost:5432/heimdall"
        )
        try:
            # Use our domain logic to create the user properly
            import uuid

            from heimdall.domain.entities import User
            from heimdall.domain.value_objects import Email, Password
            from heimdall.infrastructure.persistence.postgres.mappers import (
                user_to_db_params,
            )

            user = User.create(Email(email), Password(password))
            user.activate()  # Make user active for login

            params = user_to_db_params(user)
            await conn.execute(
                """
                INSERT INTO users (id, email, password_hash, status, is_verified,
                                 created_at, updated_at, last_login_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                uuid.UUID(params["id"]),
                params["email"],
                params["password_hash"],
                params["status"],
                params["is_verified"],
                params["created_at"],
                params["updated_at"],
                params["last_login_at"],
            )
        finally:
            await conn.close()

    asyncio.run(create_active_user())

    # Now try to login via API
    response = postgres_client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

    # Verify token works
    token = data["access_token"]
    validate_response = postgres_client.post("/auth/validate", json={"token": token})

    assert validate_response.status_code == 200
    validate_data = validate_response.json()
    assert validate_data["is_valid"] is True


def test_database_persistence_survives_restart_simulation(postgres_client):
    """Test that data persists beyond application lifecycle."""
    email = "persistent@example.com"

    # Register user
    response = postgres_client.post(
        "/auth/register",
        json={"email": email, "password": "SecurePass123"},
    )
    assert response.status_code == 200
    user_id = response.json()["user_id"]

    # Simulate application restart by verifying data exists in database
    async def verify_persistence():
        conn = await asyncpg.connect(
            "postgresql://heimdall_user:heimdall_secure_password@localhost:5432/heimdall"
        )
        try:
            user = await conn.fetchrow(
                "SELECT id, email FROM users WHERE email = $1", email
            )
            assert user is not None
            assert str(user["id"]) == user_id
            return user
        finally:
            await conn.close()

    persisted_user = asyncio.run(verify_persistence())
    assert persisted_user["email"] == email
