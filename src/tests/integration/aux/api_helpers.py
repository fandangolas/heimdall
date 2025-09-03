"""Functional API helpers for integration testing."""

import os
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient, Response

from heimdall.infrastructure.persistence.postgres.database import (
    initialize_database,
)
from heimdall.presentation.api.main import create_app
from tests.integration.aux.postgres_helpers import DATABASE_URL, cleanup_database


# Authentication endpoints
async def register_user(client: AsyncClient, email: str, password: str) -> Response:
    """Register a new user."""
    return await client.post(
        "/auth/register", json={"email": email, "password": password}
    )


async def login_user(client: AsyncClient, email: str, password: str) -> Response:
    """Login a user."""
    return await client.post("/auth/login", json={"email": email, "password": password})


async def validate_token(client: AsyncClient, token: str) -> Response:
    """Validate a JWT token."""
    return await client.post("/auth/validate", json={"token": token})


# User endpoints
async def get_current_user(client: AsyncClient, token: str) -> Response:
    """Get current user info."""
    headers = {"Authorization": f"Bearer {token}"}
    return await client.get("/auth/me", headers=headers)


# Health check endpoints
async def get_health(client: AsyncClient) -> Response:
    """Get health check."""
    return await client.get("/health")


async def get_health_detailed(client: AsyncClient) -> Response:
    """Get detailed health check."""
    return await client.get("/health/detailed")


# Service discovery
async def get_root(client: AsyncClient) -> Response:
    """Get root service information."""
    return await client.get("/")


# FastAPI test client fixture
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
