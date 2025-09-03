"""Integration tests for service discovery and API documentation queries."""

import time

import pytest

from tests.integration.aux.api_helpers import get_root

# Load fixtures from api_fixtures module
pytest_plugins = ["tests.integration.aux.api_fixtures"]


@pytest.mark.asyncio
async def test_root_endpoint_service_information(api_client):
    """Test root endpoint returns comprehensive service information."""
    # Act
    response = await get_root(api_client)

    # Assert
    assert response.status_code == 200

    data = response.json()
    required_fields = [
        "service",
        "version",
        "description",
        "docs",
        "health",
        "auth_endpoints",
    ]

    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Verify service identity
    assert data["service"] == "Heimdall Authentication Service"
    assert (
        "auth" in data["description"].lower()
        or "heimdall" in data["description"].lower()
    )

    # Verify endpoint discovery
    auth_endpoints = data["auth_endpoints"]
    expected_endpoints = ["login", "register", "validate", "me"]

    for endpoint in expected_endpoints:
        assert endpoint in auth_endpoints
        assert auth_endpoints[endpoint].startswith("/")


@pytest.mark.asyncio
async def test_openapi_documentation_available(api_client):
    """Test OpenAPI/Swagger documentation is accessible."""
    # Act
    response = await api_client.get("/docs")

    # Assert - Should return HTML for Swagger UI
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_redoc_documentation_available(api_client):
    """Test ReDoc documentation is accessible."""
    # Act
    response = await api_client.get("/redoc")

    # Assert - Should return HTML for ReDoc
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_openapi_schema_available(api_client):
    """Test OpenAPI schema JSON is accessible."""
    # Act
    response = await api_client.get("/openapi.json")

    # Assert
    assert response.status_code == 200

    data = response.json()
    assert "openapi" in data  # OpenAPI version
    assert "info" in data
    assert "paths" in data

    # Verify API info
    info = data["info"]
    assert "title" in info
    assert "heimdall" in info["title"].lower()
    assert "version" in info

    # Verify auth endpoints are documented
    paths = data["paths"]
    expected_paths = [
        "/auth/register",
        "/auth/login",
        "/auth/validate",
        "/auth/me",
        "/health",
    ]

    for path in expected_paths:
        assert path in paths, f"Missing documentation for {path}"


@pytest.mark.asyncio
async def test_service_discovery_performance(api_client):
    """Test service discovery endpoint performance."""
    # Act - Make multiple requests
    start_time = time.time()
    num_requests = 10

    for _ in range(num_requests):
        response = await get_root(api_client)
        assert response.status_code == 200

    elapsed_time = time.time() - start_time
    avg_time = elapsed_time / num_requests

    # Assert - Discovery should be fast (mostly static content)
    assert avg_time < 0.05, f"Service discovery too slow: {avg_time:.3f}s avg"


@pytest.mark.asyncio
async def test_service_metadata_completeness(api_client):
    """Test that service metadata is complete and informative."""
    # Act
    response = await get_root(api_client)

    # Assert
    assert response.status_code == 200
    data = response.json()

    # Documentation links should be valid
    docs = data["docs"]
    assert docs.startswith("/")  # Should be a URL path

    # Health endpoint should be documented
    health = data["health"]
    assert health.startswith("/")  # Should be a URL path


@pytest.mark.asyncio
async def test_api_versioning_information(api_client):
    """Test that API versioning is properly exposed."""
    # Act
    response = await get_root(api_client)

    # Assert
    assert response.status_code == 200
    data = response.json()

    # Version should be semantic
    version = data["version"]
    parts = version.split(".")
    assert len(parts) >= 2, "Version should be semantic (e.g., 1.0.0)"

    # Could check for API version in headers
    # This depends on implementation choices
    api_version = response.headers.get("X-API-Version")
    if api_version:
        assert api_version == version
