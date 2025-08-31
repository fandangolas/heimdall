"""Direct PostgreSQL repository testing."""

import asyncio

import pytest
import pytest_asyncio

from heimdall.domain.entities import User
from heimdall.domain.value_objects import Email, Password
from heimdall.infrastructure.persistence.postgres.database import (
    DatabaseManager,
    create_database_config,
)
from heimdall.infrastructure.persistence.postgres.user_repository import (
    PostgreSQLUserRepository,
)


@pytest.fixture(scope="module")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def db_manager(event_loop):
    """Create database manager for the test session."""
    config = create_database_config()
    manager = DatabaseManager(config)
    await manager.initialize()
    yield manager
    await manager.close()


@pytest_asyncio.fixture(autouse=True)
async def clean_database(db_manager):
    """Clean database before/after each test."""
    async with db_manager.get_connection() as conn:
        # Clean up tables in correct order (respecting foreign keys)
        await conn.execute("TRUNCATE TABLE sessions CASCADE;")
        await conn.execute("TRUNCATE TABLE users CASCADE;")

    yield

    async with db_manager.get_connection() as conn:
        await conn.execute("TRUNCATE TABLE sessions CASCADE;")
        await conn.execute("TRUNCATE TABLE users CASCADE;")


@pytest.mark.asyncio
async def test_user_repository_save_and_find(db_manager):
    """Test saving and finding users in PostgreSQL."""
    repo = PostgreSQLUserRepository(db_manager)

    # Create user
    user = User.create(Email("repo_test@example.com"), Password("SecurePass123"))

    # Save user
    await repo.save(user)

    # Find by email
    found_user = await repo.find_by_email(Email("repo_test@example.com"))

    assert found_user is not None
    assert found_user.email == user.email
    assert found_user.id == user.id
    assert found_user.is_active == user.is_active  # Should be inactive initially

    # Verify password hash is correct
    from heimdall.domain.value_objects.password import verify_password

    assert verify_password(Password("SecurePass123"), found_user.password_hash)


@pytest.mark.asyncio
async def test_user_repository_exists_by_email(db_manager):
    """Test checking if user exists by email."""
    repo = PostgreSQLUserRepository(db_manager)

    email = Email("exists_test@example.com")

    # Should not exist initially
    assert await repo.exists_by_email(email) is False

    # Create and save user
    user = User.create(email, Password("SecurePass123"))
    await repo.save(user)

    # Should exist now
    assert await repo.exists_by_email(email) is True


@pytest.mark.asyncio
async def test_user_repository_find_by_id(db_manager):
    """Test finding user by ID."""
    repo = PostgreSQLUserRepository(db_manager)

    # Create and save user
    user = User.create(Email("id_test@example.com"), Password("SecurePass123"))
    await repo.save(user)

    # Find by ID
    found_user = await repo.find_by_id(user.id)

    assert found_user is not None
    assert found_user.id == user.id
    assert found_user.email == user.email


@pytest.mark.asyncio
async def test_user_repository_update(db_manager):
    """Test updating existing user."""
    repo = PostgreSQLUserRepository(db_manager)

    # Create and save user
    user = User.create(Email("update_test@example.com"), Password("SecurePass123"))
    await repo.save(user)

    # Activate user (this modifies the user)
    user.activate()

    # Save updated user
    await repo.save(user)

    # Find and verify update
    found_user = await repo.find_by_email(user.email)

    assert found_user is not None
    assert found_user.is_active is True  # Should be active now


@pytest.mark.asyncio
async def test_user_repository_duplicate_email_fails(db_manager):
    """Test that duplicate emails fail due to database constraint."""
    repo = PostgreSQLUserRepository(db_manager)

    email = Email("duplicate@example.com")

    # Create and save first user
    user1 = User.create(email, Password("SecurePass123"))
    await repo.save(user1)

    # Try to save another user with same email should fail
    user2 = User.create(email, Password("DifferentPass456"))

    with pytest.raises(Exception):  # Should raise constraint error  # noqa: B017
        await repo.save(user2)
