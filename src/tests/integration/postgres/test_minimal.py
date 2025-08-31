"""Minimal PostgreSQL integration test."""

import asyncio

import pytest

from heimdall.domain.entities import User
from heimdall.domain.value_objects import Email, Password
from heimdall.infrastructure.persistence.postgres.database import (
    DatabaseManager,
    create_database_config,
)
from heimdall.infrastructure.persistence.postgres.user_repository import (
    PostgreSQLUserRepository,
)


@pytest.mark.asyncio
async def test_postgres_user_repository_basic() -> None:
    """Test PostgreSQL user repository basic functionality."""
    # Create fresh database manager
    config = create_database_config()
    db_manager = DatabaseManager(config)

    try:
        # Initialize database connection
        await db_manager.initialize()

        # Clean up any existing test data
        async with db_manager.get_connection() as conn:
            await conn.execute(
                "DELETE FROM users WHERE email = $1", "minimal_test@example.com"
            )

        # Create repository
        repo = PostgreSQLUserRepository(db_manager)

        # Test 1: Create and save user
        user = User.create(Email("minimal_test@example.com"), Password("SecurePass123"))
        await repo.save(user)
        # Test 2: Find user by email
        found_user = await repo.find_by_email(Email("minimal_test@example.com"))
        assert found_user is not None
        assert found_user.email == user.email
        assert found_user.id == user.id

        # Test 3: Check user exists
        exists = await repo.exists_by_email(Email("minimal_test@example.com"))
        assert exists is True

        # Test 4: Find user by ID
        found_by_id = await repo.find_by_id(user.id)
        assert found_by_id is not None
        assert found_by_id.id == user.id

        # Test 5: Update user (activate)
        user.activate()
        await repo.save(user)

        updated_user = await repo.find_by_email(user.email)
        assert updated_user.is_active is True

        # Clean up test data
        async with db_manager.get_connection() as conn:
            await conn.execute(
                "DELETE FROM users WHERE email = $1", "minimal_test@example.com"
            )

    finally:
        # Always close the database manager
        await db_manager.close()


if __name__ == "__main__":
    # Allow running this test directly
    asyncio.run(test_postgres_user_repository_basic())
