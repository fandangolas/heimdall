"""Query side (read operations) for CQRS."""

from .auth_queries import Dependencies as QueryDependencies
from .auth_queries import validate_token_query

__all__ = [
    "QueryDependencies",
    "validate_token_query",
]
