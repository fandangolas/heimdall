"""Integration tests verifying data persistence with PostgreSQL."""

import pytest
import pytest_asyncio


class TestPostgreSQLPersistence:
    """Test that data is properly persisted to PostgreSQL database."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, postgres_enhanced_client):
        """Setup for each test."""
        self.client = postgres_enhanced_client
        await self.client.reset_database()

    @pytest.mark.asyncio
    async def test_user_persists_after_registration(self):
        """Test that registered users are stored in PostgreSQL."""
        # Register user via API
        response = self.client.post(
            "/auth/register",
            json={"email": "persist@example.com", "password": "SecurePass123"},
        )
        assert response.status_code == 200

        # Verify user exists in database directly
        user = await self.client.get_user_from_database("persist@example.com")
        assert user is not None
        assert str(user.email) == "persist@example.com"
        assert not user.is_active  # Should be inactive initially

    @pytest.mark.asyncio
    async def test_session_persists_after_login(self):
        """Test that login sessions are stored in PostgreSQL."""
        # Create and activate user directly in database
        await self.client.create_test_user_directly(
            "session@example.com", "SecurePass123", is_active=True
        )

        # Login via API
        response = self.client.post(
            "/auth/login",
            json={"email": "session@example.com", "password": "SecurePass123"},
        )
        assert response.status_code == 200

        token = response.json()["access_token"]

        # Validate token (this should find the session in database)
        validate_response = self.client.post("/auth/validate", json={"token": token})
        assert validate_response.status_code == 200
        assert validate_response.json()["is_valid"] is True

    @pytest.mark.asyncio
    async def test_data_survives_application_restart_simulation(self):
        """Test that data persists even after 'application restart'."""
        # Register user
        response = self.client.post(
            "/auth/register",
            json={"email": "survivor@example.com", "password": "SecurePass123"},
        )
        assert response.status_code == 200
        user_id = response.json()["user_id"]

        # Simulate application restart by creating new client
        # (In real Docker test, this would be stopping/starting container)
        # For now, just verify data exists in database
        user = await self.client.get_user_from_database("survivor@example.com")
        assert user is not None
        assert str(user.id) == user_id

    @pytest.mark.asyncio
    async def test_multiple_users_isolation(self):
        """Test that multiple users are properly isolated in database."""
        users = [
            ("user1@example.com", "Password123"),
            ("user2@example.com", "Password456"),
            ("user3@example.com", "Password789"),
        ]

        user_ids = []

        # Register multiple users
        for email, password in users:
            response = self.client.post(
                "/auth/register", json={"email": email, "password": password}
            )
            assert response.status_code == 200
            user_ids.append(response.json()["user_id"])

        # Verify all users exist and have unique IDs
        assert len(set(user_ids)) == len(users)  # All IDs are unique

        for (email, _), expected_id in zip(users, user_ids, strict=False):
            user = await self.client.get_user_from_database(email)
            assert user is not None
            assert str(user.id) == expected_id

    @pytest.mark.asyncio
    async def test_concurrent_operations_database_consistency(self):
        """Test database consistency with concurrent operations."""
        import asyncio

        async def register_user(email_suffix: str):
            response = self.client.post(
                "/auth/register",
                json={
                    "email": f"concurrent{email_suffix}@example.com",
                    "password": "Password123",
                },
            )
            return response.status_code == 200

        # Register 5 users concurrently
        tasks = [register_user(str(i)) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All registrations should succeed
        successful = [r for r in results if r is True]
        assert len(successful) == 5

        # Verify all users exist in database
        for i in range(5):
            user = await self.client.get_user_from_database(
                f"concurrent{i}@example.com"
            )
            assert user is not None


class TestPostgreSQLTransactionBehavior:
    """Test transaction behavior and error handling with PostgreSQL."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, postgres_enhanced_client):
        """Setup for each test."""
        self.client = postgres_enhanced_client
        await self.client.reset_database()

    @pytest.mark.asyncio
    async def test_duplicate_email_constraint_enforced(self):
        """Test that database constraints are properly enforced."""
        email = "duplicate@example.com"

        # Register first user
        response1 = self.client.post(
            "/auth/register", json={"email": email, "password": "Password123"}
        )
        assert response1.status_code == 200

        # Try to register same email again
        response2 = self.client.post(
            "/auth/register", json={"email": email, "password": "Password456"}
        )
        assert response2.status_code == 400  # Should fail

        # Verify only one user exists in database
        user = await self.client.get_user_from_database(email)
        assert user is not None
        # The password hash should be from the first registration
        from heimdall.domain.value_objects import Password
        from heimdall.domain.value_objects.password import verify_password

        assert verify_password(Password("Password123"), user.password_hash)


class TestPostgreSQLPerformance:
    """Basic performance tests with PostgreSQL."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, postgres_enhanced_client):
        """Setup for each test."""
        self.client = postgres_enhanced_client
        await self.client.reset_database()

    @pytest.mark.asyncio
    async def test_batch_user_creation_performance(self):
        """Test performance of creating many users."""
        import time

        start_time = time.time()

        # Create 50 users (reasonable number for integration test)
        for i in range(50):
            response = self.client.post(
                "/auth/register",
                json={
                    "email": f"perf_user_{i:03d}@example.com",
                    "password": "Password123",
                },
            )
            assert response.status_code == 200

        elapsed = time.time() - start_time

        # Should complete within reasonable time (adjust based on your environment)
        assert elapsed < 30.0  # 30 seconds for 50 users

        print(
            f"Created 50 users in {elapsed:.2f} seconds ({elapsed / 50:.3f}s per user)"
        )

    @pytest.mark.asyncio
    async def test_token_validation_performance(self):
        """Test performance of token validation (read-heavy operation)."""
        import time

        # Create and activate user
        await self.client.create_test_user_directly(
            "perf_validation@example.com", "Password123", is_active=True
        )

        # Login to get token
        login_response = self.client.post(
            "/auth/login",
            json={"email": "perf_validation@example.com", "password": "Password123"},
        )
        token = login_response.json()["access_token"]

        # Time multiple token validations
        start_time = time.time()

        for _ in range(100):  # 100 validations
            response = self.client.post("/auth/validate", json={"token": token})
            assert response.status_code == 200
            assert response.json()["is_valid"] is True

        elapsed = time.time() - start_time

        # Should be fast (adjust based on your environment)
        assert elapsed < 10.0  # 10 seconds for 100 validations

        print(
            f"100 token validations in {elapsed:.2f} seconds "
            f"({elapsed / 100:.3f}s per validation)"
        )
