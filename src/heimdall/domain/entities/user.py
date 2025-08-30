"""User entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from ..value_objects import Email, Password, PasswordHash, UserId
from .session import Session


@dataclass
class User:
    """User entity - core authentication entity."""
    
    id: UserId
    email: Email
    password_hash: PasswordHash
    is_active: bool = True
    is_verified: bool = False
    permissions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: Optional[datetime] = None
    
    def authenticate(self, password: Password) -> Session:
        """Authenticate user with password."""
        if not self.is_active:
            raise ValueError("User account is inactive")
        
        if not self.password_hash.verify(password):
            raise ValueError("Invalid credentials")
        
        # Update last login time
        self.last_login_at = datetime.now(timezone.utc)
        
        # Create new session
        session = Session.create_for_user(self.id, self.email, self.permissions)
        return session
    
    def change_password(self, current_password: Password, new_password: Password) -> None:
        """Change user password."""
        if not self.password_hash.verify(current_password):
            raise ValueError("Current password is incorrect")
        
        self.password_hash = new_password.hash()
        self.updated_at = datetime.now(timezone.utc)
    
    def grant_permission(self, permission: str) -> None:
        """Grant a permission to the user."""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.now(timezone.utc)
    
    def revoke_permission(self, permission: str) -> None:
        """Revoke a permission from the user."""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.now(timezone.utc)
    
    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)
    
    def activate(self) -> None:
        """Activate user account."""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)
    
    def verify(self) -> None:
        """Mark user as verified."""
        self.is_verified = True
        self.updated_at = datetime.now(timezone.utc)
    
    @classmethod
    def create(cls, email: Email, password: Password) -> 'User':
        """Create a new user."""
        return cls(
            id=UserId.generate(),
            email=email,
            password_hash=password.hash(),
        )