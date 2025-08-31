"""PostgreSQL implementation of user repositories."""

import uuid
from typing import Any

from heimdall.domain.entities import User
from heimdall.domain.repositories.write_repositories import WriteUserRepository
from heimdall.domain.value_objects import Email, PasswordHash, UserId

from .database import DatabaseManager


class PostgreSQLUserRepository(WriteUserRepository):
    """PostgreSQL implementation of write user repository."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def find_by_email(self, email: Email) -> User | None:
        """Find user by email for authentication."""
        query = """
        SELECT id, email, password_hash, status, is_verified,
               created_at, updated_at, last_login_at
        FROM users
        WHERE email = $1
        """

        async with self.db_manager.get_connection() as conn:
            row = await conn.fetchrow(query, str(email))

        if not row:
            return None

        return self._row_to_user(row)

    async def exists_by_email(self, email: Email) -> bool:
        """Check if user exists by email."""
        query = "SELECT EXISTS(SELECT 1 FROM users WHERE email = $1)"

        async with self.db_manager.get_connection() as conn:
            result = await conn.fetchval(query, str(email))

        return bool(result)

    async def find_by_id(self, user_id: UserId) -> User | None:
        """Find user by ID."""
        query = """
        SELECT id, email, password_hash, status, is_verified,
               created_at, updated_at, last_login_at
        FROM users
        WHERE id = $1
        """

        async with self.db_manager.get_connection() as conn:
            row = await conn.fetchrow(query, uuid.UUID(str(user_id)))

        if not row:
            return None

        return self._row_to_user(row)

    async def save(self, user: User) -> None:
        """Save user (create or update)."""
        # Check if user exists
        exists_query = "SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)"

        async with self.db_manager.get_connection() as conn:
            exists = await conn.fetchval(exists_query, uuid.UUID(str(user.id)))

            if exists:
                # Update existing user
                update_query = """
                UPDATE users
                SET email = $2, password_hash = $3, status = $4,
                    is_verified = $5, last_login_at = $6, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                """
                # Map domain entity to database schema
                status = "active" if user.is_active else "inactive"
                await conn.execute(
                    update_query,
                    uuid.UUID(str(user.id)),
                    str(user.email),
                    user.password_hash.value,
                    status,
                    user.is_verified,
                    user.last_login_at,
                )
            else:
                # Insert new user
                insert_query = """
                INSERT INTO users (id, email, password_hash, status, is_verified,
                                 created_at, updated_at, last_login_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """
                # Map domain entity to database schema
                status = "active" if user.is_active else "inactive"
                await conn.execute(
                    insert_query,
                    uuid.UUID(str(user.id)),
                    str(user.email),
                    user.password_hash.value,
                    status,
                    user.is_verified,
                    user.created_at,
                    user.updated_at,
                    user.last_login_at,
                )

    def _row_to_user(self, row: dict[str, Any]) -> User:
        """Convert database row to User entity."""
        # Map database schema to domain entity
        is_active = row["status"] == "active"
        return User(
            id=UserId(str(row["id"])),
            email=Email(row["email"]),
            password_hash=PasswordHash(row["password_hash"]),
            is_active=is_active,
            is_verified=row["is_verified"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_login_at=row["last_login_at"],
        )
