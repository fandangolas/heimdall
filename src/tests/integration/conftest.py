"""PostgreSQL integration testing fixtures and configuration."""

import os
from collections.abc import AsyncIterator

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from heimdall.infrastructure.persistence.postgres.database import (
    initialize_database,
)
from heimdall.presentation.api.main import create_app

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://heimdall_user:heimdall_secure_password@localhost:5432/heimdall",
)


async def check_postgres_connection() -> bool:
    """Check if PostgreSQL is accessible."""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.close()
        return True
    except Exception as e:
        print(f"\n⚠️  PostgreSQL not accessible at {DATABASE_URL}")
        print(f"Error: {e}")
        print("\n📝 Please ensure PostgreSQL is running:")
        print("   docker-compose up -d postgres")
        print("   OR ensure your PostgreSQL service is running\n")
        return False


async def cleanup_database() -> None:
    """Clean up database for test isolation."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Delete all test data to ensure clean state
        await conn.execute("DELETE FROM sessions")
        await conn.execute("DELETE FROM users")
        await conn.execute("DELETE FROM audit_events")
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def verify_postgres():
    """Verify PostgreSQL is accessible before running tests."""
    if not await check_postgres_connection():
        pytest.exit("PostgreSQL is not accessible. Exiting tests.", 1)


@pytest_asyncio.fixture
async def api_client() -> AsyncIterator[AsyncClient]:
    """Create API client for testing."""
    # Set environment for PostgreSQL
    os.environ["PERSISTENCE_MODE"] = "postgres"
    os.environ["DATABASE_URL"] = DATABASE_URL

    # Initialize database and create app
    await initialize_database()
    app = create_app()

    # Clean database before test
    await cleanup_database()

    # Create async HTTP client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
        # Clean database after test
        await cleanup_database()
