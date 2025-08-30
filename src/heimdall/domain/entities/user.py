"""User entity."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from ..value_objects import Email, Password, PasswordHash, UserId
from ..value_objects.password import hash_password, verify_password
from ..value_objects.user_id import generate_user_id
from .session import Session


@dataclass
class User:
    """User entity - core authentication entity."""

    id: UserId
    email: Email
    password_hash: PasswordHash
    is_active: bool = True
    is_verified: bool = False
    permissions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_login_at: datetime | None = None

    def authenticate(self, password: Password) -> Session:
        """Authenticate user with password."""
        if not self.is_active:
            raise ValueError("User account is inactive")

        if not verify_password(password, self.password_hash):
            raise ValueError("Invalid credentials")

        # Update last login time
        self.last_login_at = datetime.now(UTC)

        # Create new session
        session = Session.create_for_user(self.id, self.email, self.permissions)
        return session

    def change_password(
        self, current_password: Password, new_password: Password
    ) -> None:
        """Change user password."""
        if not verify_password(current_password, self.password_hash):
            raise ValueError("Current password is incorrect")

        self.password_hash = hash_password(new_password)
        self.updated_at = datetime.now(UTC)

    def grant_permission(self, permission: str) -> None:
        """Grant a permission to the user."""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.now(UTC)

    def revoke_permission(self, permission: str) -> None:
        """Revoke a permission from the user."""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.now(UTC)

    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False
        self.updated_at = datetime.now(UTC)

    def activate(self) -> None:
        """Activate user account."""
        self.is_active = True
        self.updated_at = datetime.now(UTC)

    def verify(self) -> None:
        """Mark user as verified."""
        self.is_verified = True
        self.updated_at = datetime.now(UTC)

    @classmethod
    def create(cls, email: Email, password: Password) -> "User":
        """Create a new user."""
        return cls(
            id=generate_user_id(),
            email=email,
            password_hash=hash_password(password),
        )
