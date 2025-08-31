#!/usr/bin/env python3
"""Manual PostgreSQL integration test."""

import asyncio
import os

# Set up environment for test
os.environ["USE_POSTGRES"] = "true"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://heimdall_test_user:heimdall_test_password@localhost:5433/heimdall_test"
os.environ["PYTHONPATH"] = "/Users/silveira.nic/dev/personal/python/heimdall/src"

async def test_postgresql_connection():
    """Test basic PostgreSQL connection."""
    try:
        from heimdall.infrastructure.persistence.postgres.database import get_database_manager
        from heimdall.infrastructure.persistence.postgres.user_repository import PostgreSQLUserRepository
        from heimdall.domain.entities import User
        from heimdall.domain.value_objects import Email, Password
        
        print("🧪 Testing PostgreSQL integration...")
        
        # Get database manager
        db_manager = get_database_manager()
        await db_manager.initialize()
        print("✅ Database connection initialized")
        
        # Test user repository
        user_repo = PostgreSQLUserRepository(db_manager)
        
        # Create a test user
        test_email = "test@example.com"
        test_password = "TestPassword123"
        
        user = User.create(Email(test_email), Password(test_password))
        user.activate()  # Make user active
        
        print(f"📝 Creating test user: {test_email}")
        await user_repo.save(user)
        print("✅ User saved to database")
        
        # Retrieve the user
        retrieved_user = await user_repo.find_by_email(Email(test_email))
        if retrieved_user:
            print(f"✅ User retrieved: {retrieved_user.email}")
            print(f"   Active: {retrieved_user.is_active}")
            print(f"   ID: {retrieved_user.id}")
        else:
            print("❌ User not found")
            return False
        
        # Clean up
        await db_manager.close()
        print("✅ Database connection closed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the manual test."""
    success = await test_postgresql_connection()
    if success:
        print("🎉 Manual PostgreSQL test passed!")
        return 0
    else:
        print("💥 Manual PostgreSQL test failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)