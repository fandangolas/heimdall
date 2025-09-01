"""Base test classes for PostgreSQL integration tests."""

import pytest_asyncio


class BasePostgreSQLIntegrationTest:
    """Base class for PostgreSQL integration tests with proper async support."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup_postgres_test(self, postgres_api_client):
        """Setup PostgreSQL API client for each test."""
        self.api = postgres_api_client
        yield
        # Cleanup is handled by the postgres_api_client fixture (transaction rollback)


class BasePostgreSQLCommandTest(BasePostgreSQLIntegrationTest):
    """Base class for PostgreSQL command (write) integration tests."""


class BasePostgreSQLQueryTest(BasePostgreSQLIntegrationTest):
    """Base class for PostgreSQL query (read) integration tests."""
