"""CQRS facade - functional interface for commands and queries."""

from functools import partial

from .commands import (
    CommandDependencies,
    login_user_command,
    logout_user_command,
    register_user_command,
)
from .queries import QueryDependencies, validate_token_query


def curry_cqrs_functions(
    command_deps: CommandDependencies,
    query_deps: QueryDependencies,
):
    """Create curried CQRS functions with dependencies baked in.

    Returns a dictionary of partially applied functions that maintain
    CQRS separation while providing a unified functional interface.

    Commands (1% of traffic) use write-optimized dependencies.
    Queries (99% of traffic) use read-optimized dependencies.
    """
    # Commands - Write operations with full dependencies
    login = partial(login_user_command, deps=command_deps)
    register = partial(register_user_command, deps=command_deps)
    logout = partial(logout_user_command, deps=command_deps)

    # Queries - Read operations with minimal dependencies
    validate = partial(validate_token_query, deps=query_deps)

    return {
        # Commands (Write - 1% traffic)
        "login": login,
        "register": register,
        "logout": logout,
        # Queries (Read - 99% traffic)
        "validate": validate,
    }
