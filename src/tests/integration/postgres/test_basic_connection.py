"""Basic PostgreSQL connection test."""

import asyncpg
import pytest


@pytest.mark.asyncio
async def test_basic_postgres_connection() -> None:
    """Test basic connection to PostgreSQL database."""
    # Direct connection test
    conn = await asyncpg.connect(
        "postgresql://heimdall_user:heimdall_secure_password@localhost:5432/heimdall"
    )

    # Test basic query
    result = await conn.fetchval("SELECT 1")
    assert result == 1

    # Test that our tables exist
    tables = await conn.fetch("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)

    table_names = [row["table_name"] for row in tables]
    expected_tables = ["users", "sessions", "permissions", "roles"]

    for table in expected_tables:
        assert (
            table in table_names
        ), f"Table {table} not found. Available: {table_names}"

    await conn.close()


@pytest.mark.asyncio
async def test_user_table_structure() -> None:
    """Test that user table has correct structure."""
    conn = await asyncpg.connect(
        "postgresql://heimdall_user:heimdall_secure_password@localhost:5432/heimdall"
    )

    # Check table columns
    columns = await conn.fetch("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    """)

    column_info = {row["column_name"]: row["data_type"] for row in columns}

    # Basic column checks
    assert "id" in column_info
    assert "email" in column_info
    assert "password_hash" in column_info
    assert "status" in column_info

    await conn.close()
