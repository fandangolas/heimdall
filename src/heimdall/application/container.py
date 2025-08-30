"""Functional dependency injection container."""

from collections.abc import Callable
from typing import Any

from .services.auth_service import curry_auth_functions
from .use_cases.auth_functions import Dependencies


class Container:
    """Simple functional dependency injection container."""

    def __init__(self):
        self._instances: dict[str, Any] = {}
        self._factories: dict[str, Callable] = {}

    def register(self, name: str, factory: Callable):
        """Register a factory function."""
        self._factories[name] = factory

    def register_instance(self, name: str, instance: Any):
        """Register an instance directly."""
        self._instances[name] = instance

    def get(self, name: str) -> Any:
        """Get an instance by name."""
        if name in self._instances:
            return self._instances[name]

        if name in self._factories:
            instance = self._factories[name]()
            self._instances[name] = instance
            return instance

        raise ValueError(f"No registration found for: {name}")


def create_container() -> Container:
    """Create and configure the dependency injection container."""
    container = Container()

    # Register core services (these would be your actual implementations)
    # container.register("user_repository", lambda: InMemoryUserRepository())
    # container.register("session_repository", lambda: InMemorySessionRepository())
    # container.register("token_service", lambda: JWTTokenService())
    # container.register("event_bus", lambda: InMemoryEventBus())

    return container


def wire_auth_functions(container: Container):
    """Wire authentication functions with dependencies using partial application."""
    deps = Dependencies(
        user_repository=container.get("user_repository"),
        session_repository=container.get("session_repository"),
        token_service=container.get("token_service"),
        event_bus=container.get("event_bus"),
    )

    return curry_auth_functions(deps)


# Pure functional alternative - compose functions directly
def compose(*functions):
    """Compose functions together."""
    return lambda x: x if not functions else functions[0](compose(*functions[1:])(x))


def pipe(value, *functions):
    """Pipe a value through a series of functions."""
    for func in functions:
        value = func(value)
    return value
