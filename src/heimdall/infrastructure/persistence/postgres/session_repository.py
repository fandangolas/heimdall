"""PostgreSQL implementation of session repositories."""

from datetime import datetime, timezone
import uuid
from typing import Dict, Any

from heimdall.domain.entities import Session
from heimdall.domain.repositories.write_repositories import WriteSessionRepository
from heimdall.domain.repositories.read_repositories import ReadSessionRepository
from heimdall.domain.value_objects import Email, SessionId, UserId
from .database import DatabaseManager


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
        
        return self._row_to_session(row)
    
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
        
        # Map domain entity to database schema
        status = 'active' if session.is_active else 'invalidated'
        # Generate a simple token hash for the session (in real implementation, this would be the JWT hash)
        token_hash = f"hash_{session.id}_{session.user_id}"
        
        async with self.db_manager.get_connection() as conn:
            await conn.execute(
                insert_query,
                uuid.UUID(str(session.id)),
                uuid.UUID(str(session.user_id)),
                session.created_at,
                session.expires_at,
                status,
                token_hash
            )
    
    def _row_to_session(self, row: Dict[str, Any]) -> Session:
        """Convert database row to Session entity."""
        # Map database schema to domain entity
        is_active = row['status'] == 'active'
        
        # For now, we'll use empty permissions list - in real implementation,
        # you'd probably join with user_permissions or role_permissions tables
        return Session(
            id=SessionId(str(row['id'])),
            user_id=UserId(str(row['user_id'])),
            email=Email(row['email']),
            permissions=[],  # TODO: Load from user_permissions/role_permissions
            created_at=row['created_at'],
            expires_at=row['expires_at'],
            is_active=is_active
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
        
        # Map database schema to domain entity
        return Session(
            id=SessionId(str(row['id'])),
            user_id=UserId(str(row['user_id'])),
            email=Email(row['email']),
            permissions=[],  # TODO: Load from user_permissions/role_permissions
            created_at=row['created_at'],
            expires_at=row['expires_at'],
            is_active=True  # We already filtered for active sessions
        )