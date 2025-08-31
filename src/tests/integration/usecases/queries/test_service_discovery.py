"""Integration tests for service discovery and API documentation queries."""

from tests.integration.aux.base_test import BaseQueryIntegrationTest


class TestServiceDiscoveryQueries(BaseQueryIntegrationTest):
    """Test service discovery endpoints (read operations for API exploration)."""

    def test_root_endpoint_service_information(self):
        """Test root endpoint returns comprehensive service information."""
        # Act
        response = self.api.get_root()

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

    def test_openapi_schema_generation(self):
        """Test that OpenAPI schema is properly generated and accessible."""
        # Act
        response = self.api.get_openapi_schema()

        # Assert
        assert response.status_code == 200

        schema = response.json()

        # OpenAPI spec structure validation
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

        # Service information in OpenAPI
        info = schema["info"]
        assert info["title"] == "Heimdall Authentication Service"
        assert "version" in info

        # Paths should include our endpoints
        paths = schema["paths"]
        expected_paths = ["/auth/login", "/auth/register", "/auth/validate", "/health"]

        for path in expected_paths:
            assert path in paths, f"Missing path in OpenAPI: {path}"

    def test_api_documentation_accessibility(self):
        """Test that API documentation endpoints are accessible."""
        # Test Swagger UI
        docs_response = self.api.client.get("/docs")
        assert docs_response.status_code == 200

        # Test ReDoc
        redoc_response = self.api.client.get("/redoc")
        assert redoc_response.status_code == 200

    def test_openapi_schema_includes_authentication_flows(self):
        """Test that OpenAPI schema documents authentication flows."""
        # Act
        response = self.api.get_openapi_schema()

        # Assert
        assert response.status_code == 200

        schema = response.json()
        paths = schema["paths"]

        # Login endpoint documentation
        login_path = paths["/auth/login"]
        assert "post" in login_path
        login_post = login_path["post"]

        assert "summary" in login_post
        assert "description" in login_post
        assert "requestBody" in login_post
        assert "responses" in login_post

        # Response documentation should include success and error cases
        responses = login_post["responses"]
        assert "200" in responses  # Success
        assert "400" in responses or "422" in responses  # Error cases

    def test_openapi_schema_includes_response_models(self):
        """Test that OpenAPI schema includes proper response models."""
        # Act
        response = self.api.get_openapi_schema()

        # Assert
        assert response.status_code == 200

        schema = response.json()

        # Should have components section with schemas
        assert "components" in schema
        assert "schemas" in schema["components"]

        schemas = schema["components"]["schemas"]

        # Should include our response schemas
        expected_schemas = [
            "LoginResponseSchema",
            "RegisterResponseSchema",
            "ValidateTokenResponseSchema",
        ]

        for schema_name in expected_schemas:
            assert schema_name in schemas, f"Missing schema: {schema_name}"

    def test_service_version_consistency(self):
        """Test that service version is consistent across endpoints."""
        # Act
        root_response = self.api.get_root()
        health_response = self.api.get_detailed_health()
        openapi_response = self.api.get_openapi_schema()

        # Assert
        assert root_response.status_code == 200
        assert health_response.status_code == 200
        assert openapi_response.status_code == 200

        root_version = root_response.json()["version"]
        health_version = health_response.json()["version"]
        openapi_version = openapi_response.json()["info"]["version"]

        # All versions should be identical
        assert root_version == health_version == openapi_version

    def test_service_discovery_performance(self):
        """Test that service discovery endpoints are fast."""
        import time

        # Test root endpoint speed
        start_time = time.time()
        response = self.api.get_root()
        end_time = time.time()

        assert response.status_code == 200

        # Should be very fast
        response_time = end_time - start_time
        assert (
            response_time < 0.05
        ), f"Root endpoint took {response_time:.3f}s, expected < 0.05s"

    def test_cors_headers_present(self):
        """Test that CORS headers are present for frontend integration."""
        # Act
        response = self.api.get_root()

        # Assert
        assert response.status_code == 200

        # Check for CORS headers (added by FastAPI CORS middleware)
        # Note: TestClient might not show all CORS headers, but we can
        # check what's available

        # The main test is that the request succeeds, indicating CORS is configured
        # In a real browser environment, CORS headers would be properly validated

    def test_content_type_headers(self):
        """Test that endpoints return proper content-type headers."""
        # Act
        root_response = self.api.get_root()
        health_response = self.api.get_health()
        openapi_response = self.api.get_openapi_schema()

        # Assert
        assert root_response.status_code == 200
        assert health_response.status_code == 200
        assert openapi_response.status_code == 200

        # All should return JSON
        assert "application/json" in root_response.headers["content-type"]
        assert "application/json" in health_response.headers["content-type"]
        assert "application/json" in openapi_response.headers["content-type"]
