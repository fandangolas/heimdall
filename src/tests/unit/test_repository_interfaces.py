"""Tests for CQRS repository interface separation."""

from heimdall.application.commands.auth_commands import Dependencies as CommandDeps
from heimdall.application.queries.auth_queries import Dependencies as QueryDeps
from heimdall.domain.repositories.read_repositories import ReadSessionRepository
from heimdall.domain.repositories.write_repositories import (
    WriteSessionRepository,
    WriteUserRepository,
)


class TestRepositoryInterfaceSeparation:
    """Test that read and write repository interfaces are properly separated."""

    def test_read_session_repository_interface(self):
        """Test ReadSessionRepository has minimal read-only interface."""
        # Arrange
        interface = ReadSessionRepository

        # Act - Get all methods
        methods = [method for method in dir(interface) if not method.startswith("_")]

        # Assert - Only essential read method
        assert "find_by_id" in methods
        assert len(methods) == 1  # Only find_by_id for performance

    def test_write_session_repository_interface(self):
        """Test WriteSessionRepository has full write interface."""
        # Arrange
        interface = WriteSessionRepository

        # Act - Get all methods
        methods = [method for method in dir(interface) if not method.startswith("_")]

        # Assert - Has both read and write methods
        assert "find_by_id" in methods
        assert "save" in methods
        assert len(methods) == 2

    def test_write_user_repository_interface(self):
        """Test WriteUserRepository has comprehensive interface for commands."""
        # Arrange
        interface = WriteUserRepository

        # Act - Get all methods
        methods = [method for method in dir(interface) if not method.startswith("_")]

        # Assert - Has all methods needed for user commands
        expected_methods = {"find_by_email", "exists_by_email", "save", "find_by_id"}
        assert expected_methods.issubset(set(methods))

    def test_repository_interface_isolation(self):
        """Test that read repositories don't inherit from write repositories."""
        # Assert - ReadSessionRepository is isolated from writes
        assert not issubclass(ReadSessionRepository, WriteSessionRepository)

        # Read interface should not have write methods
        read_methods = set(dir(ReadSessionRepository))
        write_only_methods = {"save"}

        assert not any(method in read_methods for method in write_only_methods)

    def test_dependency_minimization_principle(self):
        """Test that read repositories enforce minimal dependencies principle."""
        # Command dependencies should have more fields (full context)
        command_fields = set(CommandDeps._fields)
        query_fields = set(QueryDeps._fields)

        # Assert queries have fewer dependencies than commands
        assert len(query_fields) < len(command_fields)

        # Query deps should not have user_repository or event_bus
        assert "user_repository" not in query_fields
        assert "event_bus" not in query_fields

        # But commands should have all dependencies
        assert "user_repository" in command_fields
        assert "event_bus" in command_fields
