"""PostgreSQL database connection and configuration."""

import os
from contextlib import asynccontextmanager
from dataclasses import dataclass

from asyncpg import Pool, create_pool


@dataclass(frozen=True)
class DatabaseConfig:
    """Immutable database configuration."""

    database_url: str


def create_database_config() -> DatabaseConfig:
    """Pure function to create database config from environment.

    Returns:
        Immutable DatabaseConfig instance
    """
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://heimdall_user:heimdall_secure_password@localhost:5432/heimdall",
    )

    # Remove the +asyncpg part if present
    if "+asyncpg" in database_url:
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    return DatabaseConfig(database_url=database_url)


class DatabaseManager:
    """Database connection pool manager."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pool: Pool | None = None

    async def initialize(self):
        """Initialize database connection pool."""
        self._pool = await create_pool(
            self.config.database_url,
            min_size=1,
            max_size=10,
            command_timeout=60,
            server_settings={
                "jit": "off"  # Disable JIT compilation for simpler deployment
            },
        )

    async def close(self):
        """Close database connection pool."""
        if self._pool:
            await self._pool.close()

    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool."""
        if not self._pool:
            raise RuntimeError("Database not initialized")

        async with self._pool.acquire() as connection:
            yield connection

    async def execute_query(self, query: str, *args):
        """Execute a query and return results."""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)

    async def execute_command(self, query: str, *args):
        """Execute a command (INSERT/UPDATE/DELETE) and return status."""
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)


class _DatabaseManagerSingleton:
    """Singleton for database manager."""

    def __init__(self):
        self._instance: DatabaseManager | None = None

    def get_manager(self) -> DatabaseManager:
        """Get or create the database manager."""
        if self._instance is None:
            config = create_database_config()
            self._instance = DatabaseManager(config)
        return self._instance

    async def close_manager(self):
        """Close the database manager."""
        if self._instance:
            await self._instance.close()
            self._instance = None


# Module-level singleton instance
_db_singleton = _DatabaseManagerSingleton()


def get_database_manager() -> DatabaseManager:
    """Get or create the global database manager."""
    return _db_singleton.get_manager()


async def initialize_database():
    """Initialize the database connection pool."""
    db_manager = get_database_manager()
    await db_manager.initialize()


async def close_database():
    """Close the database connection pool."""
    await _db_singleton.close_manager()
