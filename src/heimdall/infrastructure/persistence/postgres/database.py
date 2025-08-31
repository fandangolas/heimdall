"""PostgreSQL database connection and configuration."""

import os
from contextlib import asynccontextmanager

import asyncpg
from asyncpg import Pool, create_pool


class DatabaseConfig:
    """Database configuration from environment variables."""
    
    @classmethod
    def from_env(cls):
        """Create database config from environment variables."""
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://heimdall_user:heimdall_secure_password@localhost:5432/heimdall"
        )
        
        # Remove the +asyncpg part if present
        if "+asyncpg" in database_url:
            database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        
        return cls(database_url)
    
    def __init__(self, database_url: str):
        self.database_url = database_url


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
                'jit': 'off'  # Disable JIT compilation for simpler deployment
            }
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


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_database_manager() -> DatabaseManager:
    """Get or create the global database manager."""
    global _db_manager
    if _db_manager is None:
        config = DatabaseConfig.from_env()
        _db_manager = DatabaseManager(config)
    return _db_manager


async def initialize_database():
    """Initialize the database connection pool."""
    db_manager = get_database_manager()
    await db_manager.initialize()


async def close_database():
    """Close the database connection pool."""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None