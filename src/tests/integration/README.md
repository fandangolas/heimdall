# Integration Tests Structure

This directory contains integration tests organized by CQRS patterns and proper test infrastructure.

## Structure

```
src/tests/integration/
├── aux/                           # Test infrastructure and utilities
│   ├── api_client.py             # HeimdallAPIClient - FastAPI test wrapper
│   ├── base_test.py              # Base test classes with API client setup
│   ├── test_infrastructure.py     # Hybrid test infrastructure (legacy)
│   ├── test_infrastructure_demo.py # Infrastructure demo tests (legacy)
│   └── test_cqrs_integration.py  # CQRS integration tests (legacy)
│
├── postgres/                     # PostgreSQL-specific test infrastructure
│   ├── base_test.py              # PostgreSQL test base classes
│   ├── conftest.py               # PostgreSQL test fixtures
│   └── test_*.py                 # Basic PostgreSQL functionality tests
│
└── usecases/                     # Integration tests organized by CQRS
    ├── commands/                 # Write operations (1% traffic)
    │   ├── test_user_registration.py # User registration tests
    │   └── test_user_login.py        # User login tests
    │
    └── queries/                  # Read operations (99% traffic)
        ├── test_token_validation.py  # Token validation tests
        ├── test_health_checks.py     # Health check tests
        └── test_service_discovery.py # API discovery tests
```

## Design Principles

### CQRS Alignment
- **Commands**: Write operations, full dependency context, business logic validation
- **Queries**: Read operations, minimal dependencies, performance-focused

### API-First Testing
- All integration tests call actual FastAPI endpoints
- Tests use `HeimdallAPIClient` wrapper for consistent API access
- Full request/response validation including HTTP status codes

### Test Isolation
- **In-Memory Mode**: Each test starts with clean state (users, sessions, tokens cleared)
- **PostgreSQL Mode**: Database cleanup between tests for reliable isolation
- Base test classes provide automatic setup/teardown via fixtures
- Token-to-session mapping ensures correct user isolation

### Performance Testing
- Query tests include performance assertions (sub-100ms for basic operations)
- Concurrent request testing for high-throughput scenarios
- Load testing patterns for 1M+ validations/minute target

## Test Coverage

- **Commands**: 17 tests (user registration, login, validation, edge cases)
- **Queries**: 30 tests (token validation, health checks, service discovery)
- **Infrastructure**: 8 tests (API client, health checks, legacy infrastructure)
- **Total**: 55 integration tests, all calling actual FastAPI endpoints

## Dual-Mode Testing

All integration tests run in both persistence modes:

### In-Memory Mode (Default)
```bash
# Fast, no external dependencies
make test-integration
PERSISTENCE_MODE=in-memory PYTHONPATH=src python -m pytest src/tests/integration/usecases/ src/tests/integration/aux/ -v
```

### PostgreSQL Mode 
```bash
# Production-like, requires Docker
make test-postgres  
PERSISTENCE_MODE=postgres PYTHONPATH=src python -m pytest src/tests/integration/ -v
```

**Key Benefits:**
- Same test suite validates both persistence implementations
- PostgreSQL mode tests real database constraints and ACID compliance
- In-memory mode provides fast feedback without external dependencies
- Automatic container management for PostgreSQL tests