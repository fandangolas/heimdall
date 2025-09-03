"""FastAPI test fixtures for integration tests."""

import os
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from heimdall.infrastructure.persistence.postgres.database import (
    initialize_database,
)
from heimdall.presentation.api.main import create_app
from tests.integration.aux.postgres_helpers import DATABASE_URL, cleanup_database


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
