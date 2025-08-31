"""Test infrastructure for CQRS integration tests - hybrid approach."""

from unittest.mock import AsyncMock, Mock

from heimdall.application.commands import CommandDependencies
from heimdall.application.cqrs import curry_cqrs_functions
from heimdall.application.queries import QueryDependencies
from heimdall.domain.entities import Session, User
from heimdall.domain.value_objects import (
    Email,
    Password,
    Token,
    TokenClaims,
    generate_session_id,
)


class TestDatabase:
    """Simulated database with transaction-like isolation for tests."""

    def __init__(self):
        # Shared storage that persists across test methods
        self._users: dict[str, User] = {}  # email -> User
        self._sessions: dict[str, Session] = {}  # session_id -> Session

        # Transaction context - reset after each test
        self._transaction_users: dict[str, User] = {}
        self._transaction_sessions: dict[str, Session] = {}
        self._in_transaction = False

    def begin_transaction(self):
        """Start a new test transaction - isolated state."""
        self._in_transaction = True
        self._transaction_users = self._users.copy()
        self._transaction_sessions = self._sessions.copy()

    def commit_transaction(self):
        """Commit test changes to main storage."""
        if self._in_transaction:
            self._users.update(self._transaction_users)
            self._sessions.update(self._transaction_sessions)
            self._in_transaction = False

    def rollback_transaction(self):
        """Rollback test changes - clean state for next test."""
        if self._in_transaction:
            self._transaction_users.clear()
            self._transaction_sessions.clear()
            self._in_transaction = False

    def get_users(self) -> dict[str, User]:
        """Get current user storage (transaction-aware)."""
        return self._transaction_users if self._in_transaction else self._users

    def get_sessions(self) -> dict[str, Session]:
        """Get current session storage (transaction-aware)."""
        return self._transaction_sessions if self._in_transaction else self._sessions

    def reset_all(self):
        """Complete reset - use sparingly."""
        self._users.clear()
        self._sessions.clear()
        self.rollback_transaction()


class TestDependencyFactory:
    """Factory for creating test dependencies with shared infrastructure."""

    def __init__(self):
        self.db = TestDatabase()
        self._token_service = None
        self._event_bus = None

    def create_command_dependencies(self) -> CommandDependencies:
        """Create write-optimized dependencies for commands."""
        # Write repositories with full database access
        user_repo = AsyncMock()
        user_repo.find_by_email = AsyncMock(
            side_effect=lambda email: self.db.get_users().get(email.value)
        )
        user_repo.exists_by_email = AsyncMock(
            side_effect=lambda email: email.value in self.db.get_users()
        )
        user_repo.save = AsyncMock(
            side_effect=lambda user: self.db.get_users().update(
                {user.email.value: user}
            )
        )
        user_repo.find_by_id = AsyncMock(
            side_effect=lambda user_id: next(
                (u for u in self.db.get_users().values() if u.id == user_id), None
            )
        )

        session_repo = AsyncMock()
        session_repo.find_by_id = AsyncMock(
            side_effect=lambda session_id: self.db.get_sessions().get(str(session_id))
        )
        session_repo.save = AsyncMock(
            side_effect=lambda session: self.db.get_sessions().update(
                {str(session.id): session}
            )
        )

        return CommandDependencies(
            user_repository=user_repo,
            session_repository=session_repo,
            token_service=self._get_token_service(),
            event_bus=self._get_event_bus(),
        )

    def create_query_dependencies(self) -> QueryDependencies:
        """Create read-optimized dependencies for queries."""
        # Read repository with minimal interface (could be cached)
        read_session_repo = AsyncMock()
        read_session_repo.find_by_id = AsyncMock(
            side_effect=lambda session_id: self.db.get_sessions().get(str(session_id))
        )

        return QueryDependencies(
            session_repository=read_session_repo,
            token_service=self._get_token_service(),
        )

    def create_cqrs_functions(self):
        """Create curried CQRS functions with hybrid dependencies."""
        command_deps = self.create_command_dependencies()
        query_deps = self.create_query_dependencies()
        return curry_cqrs_functions(command_deps, query_deps)

    def _get_token_service(self):
        """Shared token service instance."""
        if self._token_service is None:
            self._token_service = Mock()

            def generate_token_impl(session):
                _claims = TokenClaims(
                    user_id=str(session.user_id),
                    session_id=str(session.id),
                    email=str(session.email),
                    permissions=list(session.permissions)
                    if hasattr(session, "permissions")
                    else [],
                )  # For future JWT encoding
                return Token("jwt.token.generated")

            def validate_token_impl(token):
                # Extract session info from token value for testing
                if "jwt.token.generated" in token.value:
                    # Find any valid session for testing
                    sessions = self.db.get_sessions()
                    if sessions:
                        session = next(iter(sessions.values()))
                        return TokenClaims(
                            user_id=str(session.user_id),
                            session_id=str(session.id),
                            email=str(session.email),
                            permissions=getattr(session, "permissions", []),
                        )
                raise ValueError("Invalid token")

            self._token_service.generate_token = Mock(side_effect=generate_token_impl)
            self._token_service.validate_token = Mock(side_effect=validate_token_impl)

        return self._token_service

    def _get_event_bus(self):
        """Shared event bus instance."""
        if self._event_bus is None:
            self._event_bus = AsyncMock()
            # Track published events for test assertions
            self._event_bus.published_events = []
            self._event_bus.publish = AsyncMock(
                side_effect=lambda event: self._event_bus.published_events.append(event)
            )
        return self._event_bus

    def begin_test(self):
        """Start a new test with isolated state."""
        self.db.begin_transaction()
        # Reset event tracking
        if self._event_bus:
            self._event_bus.published_events.clear()

    def end_test(self, commit: bool = False):
        """End test and cleanup state."""
        if commit:
            self.db.commit_transaction()
        else:
            self.db.rollback_transaction()

    def reset_infrastructure(self):
        """Complete reset of test infrastructure."""
        self.db.reset_all()
        if self._event_bus:
            self._event_bus.published_events.clear()
        # Keep token_service instance but reset its state if needed


class IntegrationTestBase:
    """Base class for integration tests with hybrid infrastructure."""

    @classmethod
    def setup_class(cls):
        """Setup shared test infrastructure once per test class."""
        cls.factory = TestDependencyFactory()

    def setup_method(self):
        """Setup isolated state for each test method."""
        self.factory.begin_test()
        self.auth_functions = self.factory.create_cqrs_functions()

    def teardown_method(self):
        """Cleanup after each test method."""
        self.factory.end_test(commit=False)  # Rollback by default

    @classmethod
    def teardown_class(cls):
        """Cleanup shared infrastructure after all tests."""
        cls.factory.reset_infrastructure()

    # Helper methods for common test operations
    def create_test_user(
        self, email: str = "test@example.com", password: str = "Password123"
    ) -> User:
        """Create a test user and add to database."""
        user = User.create(Email(email), Password(password))
        self.factory.db.get_users()[email] = user
        return user

    def create_test_session(self, user: User) -> Session:
        """Create a test session for user."""
        session = Mock()
        session.id = generate_session_id()
        session.user_id = user.id
        session.email = user.email
        session.is_valid = Mock(return_value=True)
        session.permissions = ["read"]

        # Mock the authenticate method on user to return this session
        user.authenticate = Mock(return_value=session)

        return session

    def get_published_events(self):
        """Get events published during the test."""
        return (
            self.factory._get_event_bus().published_events
            if self.factory._event_bus
            else []
        )
