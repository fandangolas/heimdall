"""PostgreSQL integration testing fixtures and configuration."""

import os
import subprocess
import time

import asyncpg
import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from heimdall.infrastructure.persistence.postgres.database import (
    close_database,
    initialize_database,
)
from heimdall.presentation.api.main import create_app


class PostgreSQLTestManager:
    """Manages PostgreSQL container and database lifecycle for testing."""

    def __init__(self):
        self.container_name = "heimdall-postgres"
        self.db_url = "postgresql://heimdall_user:heimdall_secure_password@localhost:5432/heimdall"
        self.container_started = False

    def start_postgres_container(self):
        """Start PostgreSQL container if not already running."""
        try:
            # Check if container is already running
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"name={self.container_name}",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            if self.container_name in result.stdout:
                print(f"✅ PostgreSQL container {self.container_name} already running")
                self.container_started = True
                return

            # Start container using docker-compose
            print("🚀 Starting PostgreSQL container...")
            subprocess.run(
                ["docker-compose", "up", "-d", "postgres"],
                check=True,
                capture_output=True,
            )

            # Wait for PostgreSQL to be ready
            print("⏳ Waiting for PostgreSQL to be ready...")
            max_attempts = 30
            for _attempt in range(max_attempts):
                try:
                    result = subprocess.run(
                        [
                            "docker",
                            "exec",
                            self.container_name,
                            "pg_isready",
                            "-U",
                            "heimdall_user",
                            "-d",
                            "heimdall",
                        ],
                        capture_output=True,
                        check=True,
                    )
                    if result.returncode == 0:
                        print("✅ PostgreSQL is ready!")
                        self.container_started = True
                        return
                except subprocess.CalledProcessError:
                    pass

                time.sleep(2)

            raise RuntimeError("PostgreSQL container failed to become ready")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to start PostgreSQL container: {e}") from e

    def stop_postgres_container(self):
        """Stop PostgreSQL container."""
        # For integration testing, we keep the container running
        # Comment out for now to avoid stopping the container between tests
        print("INFO: Keeping PostgreSQL container running for subsequent tests")

        # Original stopping code (commented out)
        # if not self.container_started:
        #     return

        # try:
        #     print("🛑 Stopping PostgreSQL container...")
        #     subprocess.run(
        #         ["docker-compose", "down"],
        #         check=True,
        #         capture_output=True
        #     )
        #     self.container_started = False
        #     print("✅ PostgreSQL container stopped")
        # except subprocess.CalledProcessError as e:
        #     print(f"⚠️ Error stopping PostgreSQL container: {e}")


class PostgreSQLAPIClient:
    """Enhanced API client for PostgreSQL integration testing."""

    def __init__(self, app):
        self.app = app
        self.client = None
        self.transport = None
        self.db_url = "postgresql://heimdall_user:heimdall_secure_password@localhost:5432/heimdall"

    async def start(self):
        """Initialize the async client and database."""
        # Initialize database connection
        await initialize_database()

        # Create async HTTP client
        self.transport = ASGITransport(app=self.app)
        self.client = AsyncClient(transport=self.transport, base_url="http://test")

    async def stop(self):
        """Clean up the client and database connections."""
        if self.client:
            await self.client.aclose()
        await close_database()

    async def begin_transaction(self):
        """Start a database transaction for test isolation."""
        self.conn = await asyncpg.connect(self.db_url)
        self.transaction = self.conn.transaction()
        await self.transaction.start()

    async def rollback_transaction(self):
        """Rollback the database transaction."""
        if hasattr(self, "transaction"):
            await self.transaction.rollback()
        if hasattr(self, "conn"):
            await self.conn.close()

    # HTTP Client Methods
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """HTTP GET request."""
        if not self.client:
            raise RuntimeError("Client not started. Call start() first.")
        return await self.client.get(url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        """HTTP POST request."""
        if not self.client:
            raise RuntimeError("Client not started. Call start() first.")
        return await self.client.post(url, **kwargs)

    # API Helper Methods
    async def register_user(self, email: str, password: str) -> httpx.Response:
        """Register a new user."""
        return await self.post(
            "/auth/register", json={"email": email, "password": password}
        )

    async def login_user(self, email: str, password: str) -> httpx.Response:
        """Login a user."""
        return await self.post(
            "/auth/login", json={"email": email, "password": password}
        )

    async def validate_token(self, token: str) -> httpx.Response:
        """Validate a JWT token."""
        return await self.post("/auth/validate", json={"token": token})

    async def get_current_user(self, token: str) -> httpx.Response:
        """Get current user info."""
        headers = {"Authorization": f"Bearer {token}"}
        return await self.get("/auth/me", headers=headers)

    async def get_health(self) -> httpx.Response:
        """Get health check."""
        return await self.get("/health")

    async def get_health_detailed(self) -> httpx.Response:
        """Get detailed health check."""
        return await self.get("/health/detailed")

    async def get_root(self) -> httpx.Response:
        """Get root service information."""
        return await self.get("/")

    # Database Helper Methods
    async def get_user_from_db(self, email: str):
        """Get user from database directly."""
        conn = await asyncpg.connect(self.db_url)
        try:
            user_row = await conn.fetchrow(
                "SELECT id, email, password_hash, status, is_verified, "
                "created_at FROM users WHERE email = $1",
                email,
            )
            return dict(user_row) if user_row else None
        finally:
            await conn.close()

    async def count_users_in_db(self) -> int:
        """Count total users in database."""
        conn = await asyncpg.connect(self.db_url)
        try:
            count = await conn.fetchval("SELECT COUNT(*) FROM users")
            return count
        finally:
            await conn.close()


# Global PostgreSQL manager instance
_postgres_manager = PostgreSQLTestManager()


@pytest.fixture(scope="session", autouse=True)
def postgres_container():
    """Session-level fixture to manage PostgreSQL container lifecycle."""
    _postgres_manager.start_postgres_container()
    yield
    _postgres_manager.stop_postgres_container()


@pytest.fixture(scope="module")
def postgres_app():
    """Create FastAPI app configured for PostgreSQL mode."""
    # Set environment for PostgreSQL
    os.environ["PERSISTENCE_MODE"] = "postgres"
    app = create_app()
    return app


@pytest_asyncio.fixture
async def postgres_api_client(postgres_app):
    """Create PostgreSQL API client with transaction-based isolation."""
    client = PostgreSQLAPIClient(postgres_app)
    await client.start()

    # Start transaction for test isolation
    await client.begin_transaction()

    yield client

    # Rollback transaction and cleanup
    await client.rollback_transaction()
    await client.stop()
