"""Integration tests for health check queries."""

import datetime
import time

import pytest

from tests.integration.aux.api_helpers import (
    get_health,
    get_health_detailed,
)

# Load fixtures from api_helpers module
pytest_plugins = ["tests.integration.aux.api_helpers"]


@pytest.mark.asyncio
async def test_basic_health_check(api_client):
    """Test basic health check endpoint."""
    # Act
    response = await get_health(api_client)

    # Assert
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data

    # Timestamp should be in ISO format
    datetime.datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))


@pytest.mark.asyncio
async def test_detailed_health_check(api_client):
    """Test detailed health check endpoint."""
    # Act
    response = await get_health_detailed(api_client)

    # Assert
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "environment" in data
    assert "system" in data
    assert "dependencies" in data
    assert "metrics" in data

    # Dependencies should include key services
    deps = data["dependencies"]
    assert "database" in deps
    assert deps["database"]["status"] == "healthy"

    # System info should be present
    system = data["system"]
    assert "python_version" in system
    assert "uptime" in system

    # Metrics should include basic stats
    metrics = data["metrics"]
    assert "total_requests" in metrics or "requests_total" in metrics
    assert "active_sessions" in metrics or "active_connections" in metrics


@pytest.mark.asyncio
async def test_health_check_performance(api_client):
    """Test health check endpoint performance."""
    # Act - Make multiple requests and measure timing
    start_time = time.time()
    num_requests = 10

    for _ in range(num_requests):
        response = await get_health(api_client)
        assert response.status_code == 200

    elapsed_time = time.time() - start_time
    avg_time = elapsed_time / num_requests

    # Assert - Health checks should be fast
    assert avg_time < 0.1, f"Health check too slow: {avg_time:.3f}s avg"


@pytest.mark.asyncio
async def test_health_check_timestamp_format(api_client):
    """Test that health check returns properly formatted timestamps."""
    # Act
    response = await get_health(api_client)

    # Assert
    assert response.status_code == 200
    data = response.json()

    # Parse timestamp - should be ISO format
    timestamp_str = data["timestamp"]
    parsed_time = datetime.datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

    # Should be recent (within last minute)
    now = datetime.datetime.now(datetime.UTC)
    time_diff = abs((now - parsed_time).total_seconds())
    assert time_diff < 60, "Timestamp not recent"


@pytest.mark.asyncio
async def test_detailed_health_check_database_status(api_client):
    """Test that detailed health check properly reports database status."""
    # Act
    response = await get_health_detailed(api_client)

    # Assert
    assert response.status_code == 200
    data = response.json()

    # Database should be reported as healthy since tests are running
    assert data["dependencies"]["database"]["status"] == "healthy"

    # Check database type is reported
    assert "type" in data["dependencies"]["database"]


@pytest.mark.asyncio
async def test_health_check_version_info(api_client):
    """Test that health check includes version information."""
    # Act
    response = await get_health(api_client)

    # Assert
    assert response.status_code == 200
    data = response.json()

    # Version should be present and follow semantic versioning
    version = data["version"]
    assert version is not None

    # Basic version format check
    parts = version.split(".")
    assert len(parts) >= 2, "Version should have at least major.minor"
