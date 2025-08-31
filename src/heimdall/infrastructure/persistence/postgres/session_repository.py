"""PostgreSQL implementation of session repositories."""

import uuid

from heimdall.domain.entities import Session
from heimdall.domain.repositories.read_repositories import ReadSessionRepository
from heimdall.domain.repositories.write_repositories import WriteSessionRepository
from heimdall.domain.value_objects import SessionId

from .database import DatabaseManager
from .mappers import row_to_session, session_to_db_params


class PostgreSQLWriteSessionRepository(WriteSessionRepository):
    """PostgreSQL implementation of write session repository."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def find_by_id(self, session_id: SessionId) -> Session | None:
        """Find session by ID for commands."""
        query = """
        SELECT s.id, s.user_id, s.created_at, s.expires_at,
               s.status, u.email
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.id = $1
        """

        async with self.db_manager.get_connection() as conn:
            row = await conn.fetchrow(query, uuid.UUID(str(session_id)))

        if not row:
            return None

        return row_to_session(row)

    async def save(self, session: Session) -> None:
        """Save session (create or update)."""
        # For simplicity, we'll always insert new sessions
        # In a real system, you might want to handle updates as well
        insert_query = """
        INSERT INTO sessions (id, user_id, created_at, expires_at, status, token_hash)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (id) DO UPDATE SET
            status = EXCLUDED.status,
            expires_at = EXCLUDED.expires_at
        """

        # Use pure function to get database parameters
        db_params = session_to_db_params(session)

        async with self.db_manager.get_connection() as conn:
            await conn.execute(
                insert_query,
                uuid.UUID(db_params["id"]),
                uuid.UUID(db_params["user_id"]),
                db_params["created_at"],
                db_params["expires_at"],
                db_params["status"],
                db_params["token_hash"],
            )


class PostgreSQLReadSessionRepository(ReadSessionRepository):
    """PostgreSQL implementation of read session repository."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def find_by_id(self, session_id: SessionId) -> Session | None:
        """Fast session lookup - optimized for token validation."""
        query = """
        SELECT s.id, s.user_id, s.created_at, s.expires_at,
               s.status, u.email
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.id = $1
            AND s.status = 'active'
            AND s.expires_at > CURRENT_TIMESTAMP
        """

        async with self.db_manager.get_connection() as conn:
            row = await conn.fetchrow(query, uuid.UUID(str(session_id)))

        if not row:
            return None

        # Use pure mapping function - note: this will detect active status from row
        session = row_to_session(row)
        # Override is_active since we already filtered for active sessions
        return Session(
            id=session.id,
            user_id=session.user_id,
            email=session.email,
            permissions=session.permissions,
            created_at=session.created_at,
            expires_at=session.expires_at,
            is_active=True,  # We already filtered for active sessions
        )
