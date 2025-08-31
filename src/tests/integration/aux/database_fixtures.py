"""Database fixtures and utilities for integration tests with PostgreSQL."""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from heimdall.infrastructure.persistence.postgres.database import (
    DatabaseManager,
    DatabaseConfig,
    get_database_manager,
    initialize_database,
    close_database
)
from heimdall.presentation.api.main import create_app


class DatabaseTestFixtures:
    """Utility class for database test management."""
    
    @staticmethod
    async def clean_all_tables(db_manager: DatabaseManager):
        """Clean all tables for test isolation."""
        cleanup_queries = [
            "TRUNCATE TABLE audit_events CASCADE;",
            "TRUNCATE TABLE password_reset_tokens CASCADE;", 
            "TRUNCATE TABLE user_permissions CASCADE;",
            "TRUNCATE TABLE user_roles CASCADE;",
            "TRUNCATE TABLE role_permissions CASCADE;",
            "TRUNCATE TABLE sessions CASCADE;",
            "TRUNCATE TABLE users CASCADE;",
            "TRUNCATE TABLE permissions CASCADE;",
            "TRUNCATE TABLE roles CASCADE;",
        ]
        
        async with db_manager.get_connection() as conn:
            for query in cleanup_queries:
                try:
                    await conn.execute(query)
                except Exception as e:
                    # Some tables might not exist or be empty, that's OK
                    print(f"Warning during cleanup: {e}")
    
    @staticmethod
    async def reset_sequences(db_manager: DatabaseManager):
        """Reset any sequences (not needed for UUID primary keys, but good practice)."""
        # Since we use UUIDs, no sequences to reset
        pass
    
    @staticmethod
    async def verify_database_schema(db_manager: DatabaseManager):
        """Verify that the database schema is properly initialized."""
        expected_tables = [
            'users', 'sessions', 'permissions', 'roles',
            'user_permissions', 'user_roles', 'role_permissions',
            'audit_events', 'password_reset_tokens'
        ]
        
        async with db_manager.get_connection() as conn:
            for table in expected_tables:
                result = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                    table
                )
                if not result:
                    raise RuntimeError(f"Expected table '{table}' not found in database")
        
        print("✅ Database schema verification passed")


@pytest_asyncio.fixture(scope="session")
async def database_manager() -> AsyncGenerator[DatabaseManager, None]:
    """Session-scoped database manager for integration tests."""
    # Ensure we're using the test database
    test_db_url = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://heimdall_test_user:heimdall_test_password@localhost:5433/heimdall_test"
    )
    
    # Override the global database manager for tests
    config = DatabaseConfig(test_db_url)
    db_manager = DatabaseManager(config)
    
    try:
        await db_manager.initialize()
        await DatabaseTestFixtures.verify_database_schema(db_manager)
        yield db_manager
    finally:
        await db_manager.close()


@pytest_asyncio.fixture(autouse=True)
async def clean_database(database_manager: DatabaseManager):
    """Auto-cleanup database between tests for isolation."""
    # Clean before each test
    await DatabaseTestFixtures.clean_all_tables(database_manager)
    yield
    # Clean after each test as well
    await DatabaseTestFixtures.clean_all_tables(database_manager)


@pytest.fixture
def postgres_api_client(database_manager) -> TestClient:
    """Test client configured to use PostgreSQL repositories."""
    # Set environment to use PostgreSQL
    original_postgres = os.environ.get("USE_POSTGRES")
    os.environ["USE_POSTGRES"] = "true"
    
    try:
        app = create_app()
        client = TestClient(app)
        return client
    finally:
        # Restore original setting
        if original_postgres is not None:
            os.environ["USE_POSTGRES"] = original_postgres
        else:
            os.environ.pop("USE_POSTGRES", None)


class PostgreSQLAPIClient:
    """Enhanced API client for PostgreSQL integration tests."""
    
    def __init__(self, client: TestClient, db_manager: DatabaseManager):
        self.client = client
        self.db_manager = db_manager
    
    async def reset_database(self):
        """Reset database state between tests."""
        await DatabaseTestFixtures.clean_all_tables(self.db_manager)
    
    async def create_test_user_directly(self, email: str, password: str, is_active: bool = True):
        """Create a user directly in the database for test setup."""
        from heimdall.domain.entities import User
        from heimdall.domain.value_objects import Email, Password
        from heimdall.infrastructure.persistence.postgres.user_repository import PostgreSQLUserRepository
        
        user = User.create(Email(email), Password(password))
        if is_active:
            user.activate()
        
        repo = PostgreSQLUserRepository(self.db_manager)
        await repo.save(user)
        return user
    
    async def get_user_from_database(self, email: str):
        """Get user directly from database for verification."""
        from heimdall.domain.value_objects import Email
        from heimdall.infrastructure.persistence.postgres.user_repository import PostgreSQLUserRepository
        
        repo = PostgreSQLUserRepository(self.db_manager)
        return await repo.find_by_email(Email(email))
    
    # Proxy all HTTP methods to the underlying client
    def __getattr__(self, name):
        return getattr(self.client, name)


@pytest.fixture
def postgres_enhanced_client(postgres_api_client, database_manager) -> PostgreSQLAPIClient:
    """Enhanced API client with database utilities."""
    return PostgreSQLAPIClient(postgres_api_client, database_manager)