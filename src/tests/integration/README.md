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
- Each test starts with clean state (users, sessions, tokens cleared)
- Base test classes provide automatic setup/teardown via fixtures
- Token-to-session mapping ensures correct user isolation

### Performance Testing
- Query tests include performance assertions (sub-100ms for basic operations)
- Concurrent request testing for high-throughput scenarios
- Load testing patterns for 1M+ validations/minute target

## Test Coverage

- **Commands**: 15 tests (user registration, login, validation, edge cases)
- **Queries**: 30 tests (token validation, health checks, service discovery)
- **Total**: 45 integration tests, all calling actual FastAPI endpoints