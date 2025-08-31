"""Base test classes for integration tests."""

import pytest

from .api_client import HeimdallAPIClient


class BaseIntegrationTest:
    """Base class for integration tests with API client setup."""

    @pytest.fixture(autouse=True)
    def setup_api_client(self):
        """Setup API client before each test."""
        self.api = HeimdallAPIClient()
        yield
        # Cleanup after test
        self.api.reset()


class BaseCommandIntegrationTest(BaseIntegrationTest):
    """Base class for command (write) integration tests."""


class BaseQueryIntegrationTest(BaseIntegrationTest):
    """Base class for query (read) integration tests."""
