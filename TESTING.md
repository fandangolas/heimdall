# Heimdall Testing Guide

This guide covers how to run integration tests with real PostgreSQL instances using Docker.

## Overview

Heimdall supports multiple testing approaches:

1. **Unit Tests** - Fast tests with no external dependencies
2. **Integration Tests (Mock)** - API tests using in-memory mock repositories  
3. **PostgreSQL Integration Tests** - Full-stack tests with real database persistence

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.13+
- Make (optional, for convenient commands)

### Running Tests

```bash
# Quick unit tests (fastest)
make test

# All tests with PostgreSQL (most comprehensive)
make test-postgres

# Using scripts directly
./scripts/test-local.sh unit
./scripts/run-integration-tests.sh --postgres --verbose
```

## Test Suites

### 1. Unit Tests (Fast)

```bash
# Local execution (no Docker required)
make test-unit
# or
./scripts/test-local.sh unit

# Results in ~10 seconds
```

**What they test:**
- Domain entities and value objects
- Business logic and CQRS functions
- Repository interfaces (without actual databases)

### 2. Mock Integration Tests  

```bash
# Local execution with mock repositories
make test-integration
# or
./scripts/test-local.sh integration
```

**What they test:**
- Full API endpoints
- Request/response serialization
- End-to-end authentication flows
- Uses in-memory mock repositories

### 3. PostgreSQL Integration Tests

```bash
# Requires Docker
make test-postgres
# or
./scripts/run-integration-tests.sh --postgres
```

**What they test:**
- Data persistence and retrieval
- Database constraints and transactions
- Performance with real database queries
- Container orchestration

## Docker Test Environment

### Architecture

```
┌─────────────────┐    ┌──────────────────┐
│   Test Runner   │────│   Heimdall API   │
│   (pytest)      │    │   Container      │
└─────────────────┘    └──────────────────┘
                              │
                              │
                       ┌──────────────────┐
                       │   PostgreSQL     │
                       │   Test Database  │
                       └──────────────────┘
```

### Configuration

The test environment uses:

- **PostgreSQL 16 Alpine** - Lightweight, fast startup
- **Test Database**: `heimdall_test` (separate from development)
- **Test Port**: `5433` (avoids conflicts with development database)
- **Optimized Settings**: Reduced durability for faster tests
- **tmpfs Storage**: In-memory database for maximum speed

### Test Database Features

- **Automatic Schema Setup** - Runs `migrations/init.sql` on startup
- **Test Isolation** - Database cleaned between tests
- **Performance Optimized** - Special PostgreSQL settings for testing
- **Health Checks** - Ensures database is ready before running tests

## Running Specific Test Categories

### PostgreSQL-Specific Tests

```bash
# Run only database persistence tests
./scripts/run-integration-tests.sh --postgres

# Keep containers running for debugging
./scripts/run-integration-tests.sh --postgres --keep

# Verbose output with coverage
./scripts/run-integration-tests.sh --postgres --verbose
```

### All Test Suites

```bash
# Run everything: unit, integration, and PostgreSQL tests
./scripts/run-integration-tests.sh --all

# With coverage reporting
./scripts/run-integration-tests.sh --all --verbose
```

## Test Configuration

### Environment Variables

```bash
# Test-specific settings
export POSTGRES_TEST_PASSWORD=heimdall_test_password
export DATABASE_URL=postgresql+asyncpg://heimdall_test_user:heimdall_test_password@localhost:5433/heimdall_test
export USE_POSTGRES=true
export ENVIRONMENT=test
```

### Test Results

Test results are saved in `./test-results/`:

```
test-results/
├── junit.xml              # JUnit test results
├── coverage.xml            # Coverage report
├── htmlcov/               # HTML coverage report
├── unit-junit.xml         # Unit test results
├── integration-junit.xml  # Integration test results  
└── postgres-junit.xml     # PostgreSQL test results
```

## Debugging Failed Tests

### 1. Keep Containers Running

```bash
./scripts/run-integration-tests.sh --postgres --keep
```

This leaves containers running so you can:

```bash
# Connect to test database
psql -h localhost -p 5433 -U heimdall_test_user -d heimdall_test

# Check container logs
docker-compose -f docker-compose.test.yml logs test-postgres
docker-compose -f docker-compose.test.yml logs heimdall-test
```

### 2. Verbose Test Output

```bash
./scripts/run-integration-tests.sh --postgres --verbose
```

### 3. Run Individual Tests

```bash
# Run specific test file
docker-compose -f docker-compose.test.yml run --rm heimdall-test \
    pytest src/tests/integration/postgres/test_database_persistence.py::TestPostgreSQLPersistence::test_user_persists_after_registration -v

# Run with debugging
docker-compose -f docker-compose.test.yml run --rm heimdall-test \
    pytest src/tests/integration/postgres/ -v -s --pdb
```

## Performance Testing

### Database Performance Tests

The PostgreSQL test suite includes performance benchmarks:

```bash
# Run performance tests specifically
docker-compose -f docker-compose.test.yml run --rm heimdall-test \
    pytest src/tests/integration/postgres/test_database_persistence.py::TestPostgreSQLPerformance -v
```

**Benchmarks include:**
- Batch user creation (50 users)
- Token validation performance (100 validations)  
- Concurrent operation consistency

### Expected Performance

On a typical development machine:

- **User Registration**: ~0.1s per user
- **Token Validation**: ~0.05s per validation
- **Database Cleanup**: ~0.5s per test

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run PostgreSQL Integration Tests
        run: |
          chmod +x scripts/run-integration-tests.sh
          ./scripts/run-integration-tests.sh --all --verbose
          
      - name: Upload Test Results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: test-results/
```

## Troubleshooting

### Common Issues

1. **Docker not running**
   ```bash
   # Start Docker Desktop or Docker daemon
   sudo systemctl start docker  # Linux
   ```

2. **Port conflicts**
   ```bash
   # Check if port 5433 is in use
   lsof -i :5433
   
   # Change test port in docker-compose.test.yml if needed
   ```

3. **Database connection issues**
   ```bash
   # Check database health
   docker-compose -f docker-compose.test.yml exec test-postgres pg_isready -U heimdall_test_user -d heimdall_test
   ```

4. **Test isolation issues**
   ```bash
   # Force clean database state
   docker-compose -f docker-compose.test.yml down -v
   docker-compose -f docker-compose.test.yml up -d test-postgres
   ```

### Clean Slate

```bash
# Complete cleanup and restart
docker-compose -f docker-compose.test.yml down -v --remove-orphans
docker system prune -f
make clean
./scripts/run-integration-tests.sh --postgres
```

## Test Development

### Adding New PostgreSQL Tests

1. Create test file in `src/tests/integration/postgres/`
2. Use fixtures from `database_fixtures.py`
3. Follow naming convention: `test_*.py`

Example:

```python
import pytest
from tests.integration.aux.database_fixtures import postgres_enhanced_client

class TestMyNewFeature:
    @pytest.mark.asyncio
    async def test_my_feature(self, postgres_enhanced_client):
        # Test with real PostgreSQL database
        await postgres_enhanced_client.reset_database()
        
        # Your test logic here
        pass
```

### Custom Test Fixtures

See `src/tests/integration/aux/database_fixtures.py` for:

- `database_manager` - PostgreSQL connection
- `clean_database` - Automatic cleanup between tests  
- `postgres_enhanced_client` - API client with database utilities

This comprehensive testing setup ensures that your integration tests run reliably with real PostgreSQL instances, providing confidence that the application works correctly in production-like environments.