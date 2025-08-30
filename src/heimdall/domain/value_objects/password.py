"""Password value objects - functional approach."""

from typing import NamedTuple

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordValue(NamedTuple):
    """Raw password value object."""

    value: str

    def __str__(self) -> str:
        """String representation (masked for security)."""
        return "********"


class PasswordHashValue(NamedTuple):
    """Hashed password value object."""

    value: str

    def __str__(self) -> str:
        """String representation."""
        return f"PasswordHash(...{self.value[-6:]})"


def Password(password_string: str) -> PasswordValue:
    """Create and validate a password value object."""
    MIN_LENGTH = 8

    if not password_string:
        raise ValueError("Password cannot be empty")

    if len(password_string) < MIN_LENGTH:
        raise ValueError(f"Password must be at least {MIN_LENGTH} characters long")

    # Check for at least one uppercase, one lowercase, one digit
    has_upper = any(c.isupper() for c in password_string)
    has_lower = any(c.islower() for c in password_string)
    has_digit = any(c.isdigit() for c in password_string)

    if not (has_upper and has_lower and has_digit):
        raise ValueError(
            "Password must contain at least one uppercase letter, "
            "one lowercase letter, and one digit"
        )

    return PasswordValue(value=password_string)


def PasswordHash(hash_string: str) -> PasswordHashValue:
    """Create a password hash value object."""
    if not hash_string:
        raise ValueError("Password hash cannot be empty")

    return PasswordHashValue(value=hash_string)


def hash_password(password: PasswordValue) -> PasswordHashValue:
    """Hash a password."""
    return PasswordHash(pwd_context.hash(password.value))


def verify_password(password: PasswordValue, password_hash: PasswordHashValue) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(password.value, password_hash.value)
