"""PostgreSQL-specific helpers for integration tests."""

import os

import asyncpg
import pytest

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


async def verify_postgres():
    """Verify PostgreSQL is accessible before running tests."""
    if not await check_postgres_connection():
        pytest.exit("PostgreSQL is not accessible. Exiting tests.", 1)
