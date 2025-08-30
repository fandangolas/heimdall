"""Functional authentication service."""

from functools import partial

from ..use_cases.auth_functions import (
    Dependencies,
    login_user,
    logout_user,
    register_user,
    validate_token,
)


def curry_auth_functions(deps: Dependencies):
    """Create curried authentication functions with dependencies baked in."""
    # Create partially applied functions with deps
    login = partial(login_user, deps=deps)
    register = partial(register_user, deps=deps)
    logout = partial(logout_user, deps=deps)
    validate = partial(validate_token, deps=deps)

    return {
        "login": login,
        "register": register,
        "logout": logout,
        "validate": validate,
    }
