"""Password value objects."""

from dataclasses import dataclass
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass(frozen=True)
class Password:
    """Raw password value object with validation."""
    
    value: str
    
    MIN_LENGTH = 8
    
    def __post_init__(self) -> None:
        """Validate password strength."""
        if not self.value:
            raise ValueError("Password cannot be empty")
        
        if len(self.value) < self.MIN_LENGTH:
            raise ValueError(f"Password must be at least {self.MIN_LENGTH} characters long")
        
        # Check for at least one uppercase, one lowercase, one digit
        has_upper = any(c.isupper() for c in self.value)
        has_lower = any(c.islower() for c in self.value)
        has_digit = any(c.isdigit() for c in self.value)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, and one digit"
            )
    
    def hash(self) -> 'PasswordHash':
        """Hash the password."""
        return PasswordHash(pwd_context.hash(self.value))
    
    def __str__(self) -> str:
        """String representation (masked for security)."""
        return "********"


@dataclass(frozen=True)
class PasswordHash:
    """Hashed password value object."""
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate hash format."""
        if not self.value:
            raise ValueError("Password hash cannot be empty")
    
    def verify(self, password: Password) -> bool:
        """Verify a password against this hash."""
        return pwd_context.verify(password.value, self.value)
    
    def __str__(self) -> str:
        """String representation."""
        return f"PasswordHash(...{self.value[-6:]})"