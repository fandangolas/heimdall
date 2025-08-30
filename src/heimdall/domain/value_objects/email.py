"""Email value object."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """Email value object with validation."""

    value: str

    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def __post_init__(self) -> None:
        """Validate email format after initialization."""
        if not self.value:
            raise ValueError("Email cannot be empty")

        if not self.EMAIL_REGEX.match(self.value):
            raise ValueError(f"Invalid email format: {self.value}")

        # Normalize email to lowercase
        object.__setattr__(self, "value", self.value.lower())

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def domain(self) -> str:
        """Get the domain part of the email."""
        return self.value.split("@")[1]
