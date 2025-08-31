"""Functional authentication service using CQRS."""

from ..commands import CommandDependencies
from ..cqrs import curry_cqrs_functions
from ..queries import QueryDependencies


def curry_auth_functions(
    command_deps: CommandDependencies,
    query_deps: QueryDependencies,
):
    """Create curried authentication functions with CQRS dependencies baked in.

    This is now a wrapper around the CQRS functions for any remaining consumers.
    """
    return curry_cqrs_functions(command_deps, query_deps)
