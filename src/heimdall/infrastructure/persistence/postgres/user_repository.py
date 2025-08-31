"""PostgreSQL implementation of user repositories."""

import uuid

from heimdall.domain.entities import User
from heimdall.domain.repositories.write_repositories import WriteUserRepository
from heimdall.domain.value_objects import Email, UserId

from .database import DatabaseManager
from .mappers import row_to_user, user_to_db_params


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

        return row_to_user(row)

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

        return row_to_user(row)

    async def save(self, user: User) -> None:
        """Save user (create or update)."""
        # Check if user exists
        exists_query = "SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)"

        # Use pure function to get database parameters
        db_params = user_to_db_params(user)

        async with self.db_manager.get_connection() as conn:
            exists = await conn.fetchval(exists_query, uuid.UUID(db_params["id"]))

            if exists:
                # Update existing user
                update_query = """
                UPDATE users
                SET email = $2, password_hash = $3, status = $4,
                    is_verified = $5, last_login_at = $6, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                """
                await conn.execute(
                    update_query,
                    uuid.UUID(db_params["id"]),
                    db_params["email"],
                    db_params["password_hash"],
                    db_params["status"],
                    db_params["is_verified"],
                    db_params["last_login_at"],
                )
            else:
                # Insert new user
                insert_query = """
                INSERT INTO users (id, email, password_hash, status, is_verified,
                                 created_at, updated_at, last_login_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """
                await conn.execute(
                    insert_query,
                    uuid.UUID(db_params["id"]),
                    db_params["email"],
                    db_params["password_hash"],
                    db_params["status"],
                    db_params["is_verified"],
                    db_params["created_at"],
                    db_params["updated_at"],
                    db_params["last_login_at"],
                )
