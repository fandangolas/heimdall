"""Shared API client infrastructure for integration tests."""

from fastapi.testclient import TestClient

from heimdall.presentation.api.dependencies import (
    _EVENTS,
    _SESSIONS,
    _TOKEN_TO_SESSION,
    _USERS,
)
from heimdall.presentation.api.main import app


class HeimdallAPIClient:
    """Test client wrapper for Heimdall API with convenient methods."""

    def __init__(self):
        """Initialize the test client."""
        self.client = TestClient(app)
        self._clear_state()

    def _clear_state(self):
        """Clear global state to ensure test isolation."""
        _USERS.clear()
        _SESSIONS.clear()
        _EVENTS.clear()
        _TOKEN_TO_SESSION.clear()

    def reset(self):
        """Reset client state between tests."""
        self._clear_state()

    # Root and Health endpoints
    def get_root(self):
        """Get root service information."""
        return self.client.get("/")

    def get_health(self):
        """Get basic health check."""
        return self.client.get("/health")

    def get_detailed_health(self):
        """Get detailed health check."""
        return self.client.get("/health/detailed")

    def get_ready(self):
        """Get readiness probe."""
        return self.client.get("/ready")

    def get_live(self):
        """Get liveness probe."""
        return self.client.get("/live")

    # Command endpoints (write operations)
    def register_user(self, email: str, password: str):
        """Register a new user."""
        return self.client.post(
            "/auth/register", json={"email": email, "password": password}
        )

    def login_user(self, email: str, password: str):
        """Login user and get access token."""
        return self.client.post(
            "/auth/login", json={"email": email, "password": password}
        )

    # Query endpoints (read operations)
    def validate_token(self, token: str):
        """Validate an access token."""
        return self.client.post("/auth/validate", json={"token": token})

    def get_current_user(self, token: str):
        """Get current user info using Authorization header."""
        return self.client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    # OpenAPI schema
    def get_openapi_schema(self):
        """Get OpenAPI schema."""
        return self.client.get("/openapi.json")

    # Convenience methods for full flows
    def register_and_login(self, email: str, password: str):
        """Register user and login, return token."""
        register_response = self.register_user(email, password)
        if register_response.status_code != 200:
            raise Exception(f"Registration failed: {register_response.json()}")

        login_response = self.login_user(email, password)
        if login_response.status_code != 200:
            raise Exception(f"Login failed: {login_response.json()}")

        return login_response.json()["access_token"]
