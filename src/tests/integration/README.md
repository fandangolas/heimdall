# Integration Test Infrastructure

## Hybrid Approach Benefits

Our integration tests use a **hybrid infrastructure pattern** that combines:

- **Shared Infrastructure**: Dependencies, services, and repositories
- **Isolated State**: Each test gets clean, transaction-like state  
- **Automatic Cleanup**: State automatically resets between tests

## Before vs After Refactoring

### Before (Manual Setup)
```python
# Every test had to manually create all dependencies
async def test_login_flow():
    # 40+ lines of manual mock setup
    user_repo = AsyncMock()
    session_repo = AsyncMock() 
    token_service = Mock()
    event_bus = AsyncMock()
    shared_sessions = {}  # Manual state management
    
    # Complex mock side effects
    user_repo.find_by_email.return_value = user
    session_repo.save.side_effect = lambda s: shared_sessions.update({s.id: s})
    # ... many more lines
    
    # Manual dependency injection
    command_deps = CommandDependencies(user_repo, session_repo, token_service, event_bus)
    query_deps = QueryDependencies(session_repo, token_service)
    
    # Test logic finally starts...
```

### After (Hybrid Infrastructure)
```python  
class TestCQRSIntegration(IntegrationTestBase):
    async def test_login_flow(self):
        # Clean, focused test logic
        user = self.create_test_user("test@example.com", "Password123")
        session = self.create_test_session(user)
        
        # Test the actual behavior
        response = await self.auth_functions["login"](request)
        
        # Simple, clear assertions
        assert response.access_token == "jwt.token.generated"
        assert len(self.get_published_events()) == 1
```

## Key Infrastructure Components

### `TestDatabase` - Transaction-like Isolation
- **Shared Storage**: Persists across test methods in a class
- **Transaction Context**: Each test gets isolated state copy
- **Automatic Rollback**: State automatically resets after each test

### `TestDependencyFactory` - Shared Infrastructure
- **Singleton Services**: Token service and event bus reused
- **Mock Repositories**: Connected to shared database simulation
- **CQRS Support**: Separate command/query dependency creation

### `IntegrationTestBase` - Test Lifecycle Management
- **Setup**: Creates fresh CQRS functions for each test
- **Teardown**: Automatically resets state via rollback
- **Helpers**: Common operations like `create_test_user()`

## Benefits Achieved

✅ **90% Less Boilerplate**: Tests focus on behavior, not setup  
✅ **Perfect Isolation**: Each test starts with clean state  
✅ **Reusable Infrastructure**: Shared services, individual state  
✅ **Realistic Testing**: Simulates database transactions  
✅ **Easy Debugging**: Clear test structure and helper methods  
✅ **Parallel Ready**: Transaction-like isolation enables parallelism  

## Usage Patterns

### Basic Test
```python
async def test_simple_operation(self):
    user = self.create_test_user()  # Helper creates and stores
    result = await self.auth_functions["login"](request)  # Ready to use
    assert result.success  # Clean assertions
```

### State Verification
```python  
async def test_state_changes(self):
    # Perform operations
    await self.auth_functions["register"](request)
    
    # Verify state across CQRS boundaries
    users = self.factory.db.get_users()
    events = self.get_published_events()
    
    assert len(users) == 1
    assert len(events) == 1
```

### Concurrent Operations
```python
async def test_parallel_operations(self):
    user1 = self.create_test_user("user1@test.com")
    user2 = self.create_test_user("user2@test.com")
    
    # Both operations work on isolated but shared state
    results = await asyncio.gather(
        self.auth_functions["login"](request1),
        self.auth_functions["login"](request2)
    )
    
    # State is correctly maintained for both
    assert len(self.factory.db.get_sessions()) == 2
```

This infrastructure makes integration testing **maintainable, reliable, and realistic** while keeping the focus on testing business logic rather than test infrastructure.