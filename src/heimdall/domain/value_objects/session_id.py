"""Session ID value object."""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class SessionId:
    """Session identifier value object."""
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate session ID format."""
        if not self.value:
            raise ValueError("Session ID cannot be empty")
        
        # Validate UUID format
        try:
            uuid.UUID(self.value)
        except ValueError:
            raise ValueError(f"Invalid session ID format: {self.value}")
    
    @classmethod
    def generate(cls) -> 'SessionId':
        """Generate a new session ID."""
        return cls(str(uuid.uuid4()))
    
    def __str__(self) -> str:
        """String representation."""
        return self.value