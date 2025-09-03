"""Functional API helpers for integration testing."""

from httpx import AsyncClient, Response


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
