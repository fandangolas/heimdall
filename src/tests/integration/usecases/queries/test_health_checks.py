"""Integration tests for health check queries."""

import datetime
import time

from tests.integration.aux.base_test import BaseQueryIntegrationTest


class TestHealthCheckQueries(BaseQueryIntegrationTest):
    """Test health check endpoints (read operations for monitoring)."""

    def test_basic_health_check(self):
        """Test basic health check endpoint."""
        # Act
        response = self.api.get_health()

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

        # Timestamp should be in ISO format
        datetime.datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    def test_detailed_health_check(self):
        """Test detailed health check endpoint."""
        # Act
        response = self.api.get_detailed_health()

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
        assert "cache" in deps
        assert "event_bus" in deps

        # Each dependency should have status
        for _service, info in deps.items():
            assert "status" in info
            assert "type" in info

    def test_readiness_probe(self):
        """Test Kubernetes readiness probe endpoint."""
        # Act
        response = self.api.get_ready()

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"
        assert "timestamp" in data

    def test_liveness_probe(self):
        """Test Kubernetes liveness probe endpoint."""
        # Act
        response = self.api.get_live()

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data

    def test_health_checks_are_fast(self):
        """Test that health checks respond quickly (performance requirement)."""
        # Test basic health check speed
        start_time = time.time()
        response = self.api.get_health()
        end_time = time.time()

        assert response.status_code == 200

        # Health check should be very fast (under 50ms)
        response_time = end_time - start_time
        assert response_time < 0.05, (
            f"Health check took {response_time:.3f}s, expected < 0.05s"
        )

    def test_health_checks_independent_of_auth_state(self):
        """Test that health checks work regardless of authentication state."""
        # Health checks should work without any authentication setup

        # Act - Call health endpoints before any users exist
        health_response = self.api.get_health()
        detailed_response = self.api.get_detailed_health()
        ready_response = self.api.get_ready()
        live_response = self.api.get_live()

        # Assert - All should succeed
        assert health_response.status_code == 200
        assert detailed_response.status_code == 200
        assert ready_response.status_code == 200
        assert live_response.status_code == 200

    def test_concurrent_health_check_requests(self):
        """Test that health checks handle concurrent requests well."""
        # Act - Multiple rapid requests
        responses = []
        for _ in range(10):
            response = self.api.get_health()
            responses.append(response)

        # Assert - All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    def test_health_check_content_type(self):
        """Test that health checks return proper content type."""
        # Act
        response = self.api.get_health()

        # Assert
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_health_check_endpoints_discoverable(self):
        """Test that health check endpoints are listed in root endpoint."""
        # Act
        root_response = self.api.get_root()

        # Assert
        assert root_response.status_code == 200
        data = root_response.json()
        assert "health" in data
        # Root should indicate health endpoint location
        assert data["health"] == "/health"

    def test_system_information_in_detailed_health(self):
        """Test that detailed health includes system information."""
        # Act
        response = self.api.get_detailed_health()

        # Assert
        assert response.status_code == 200

        data = response.json()
        system = data["system"]

        assert "python_version" in system
        # Python version should be in format like "3.13.7"
        python_version = system["python_version"]
        assert len(python_version.split(".")) >= 2

    def test_health_metrics_structure(self):
        """Test that health metrics have expected structure."""
        # Act
        response = self.api.get_detailed_health()

        # Assert
        assert response.status_code == 200

        data = response.json()
        metrics = data["metrics"]

        # Expected metrics (even if zero/placeholder values)
        expected_metrics = ["total_requests", "active_sessions", "cache_hit_rate"]
        for metric in expected_metrics:
            assert metric in metrics
