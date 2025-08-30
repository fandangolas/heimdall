"""Email value object - functional approach."""

import re
from typing import NamedTuple

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class EmailValue(NamedTuple):
    """Immutable email value object."""

    value: str
    domain: str

    def __str__(self) -> str:
        """String representation."""
        return self.value


def Email(email_string: str) -> EmailValue:
    """Create and validate an email value object."""
    if not email_string:
        raise ValueError("Email cannot be empty")

    # Normalize to lowercase
    normalized = email_string.lower()

    if not EMAIL_REGEX.match(normalized):
        raise ValueError(f"Invalid email format: {email_string}")

    domain = normalized.split("@")[1]

    return EmailValue(value=normalized, domain=domain)
