"""Functional dependency injection container."""

from collections.abc import Callable
from typing import Any

from .commands import CommandDependencies
from .cqrs import curry_cqrs_functions
from .queries import QueryDependencies


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
    """Wire authentication functions with CQRS dependencies using partial application."""
    # Command dependencies - for write operations
    command_deps = CommandDependencies(
        user_repository=container.get("write_user_repository"),
        session_repository=container.get("write_session_repository"),
        token_service=container.get("token_service"),
        event_bus=container.get("event_bus"),
    )

    # Query dependencies - for read operations
    query_deps = QueryDependencies(
        session_repository=container.get("read_session_repository"),
        token_service=container.get("token_service"),
    )

    return curry_cqrs_functions(command_deps, query_deps)
