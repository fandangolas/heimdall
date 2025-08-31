# Heimdall Testing Guide

This document describes the test architecture and how to run different test suites.

## Test Architecture

Heimdall uses a **dual-persistence architecture** with separate test environments:

### 🔬 Unit Tests (Fast, Isolated)
- **Purpose**: Test domain logic, entities, value objects, and use cases
- **Persistence**: Always uses `PERSISTENCE_MODE=in-memory`
- **Dependencies**: No external services required
- **Speed**: ~5 seconds for 87 tests
- **Isolation**: Each test is completely isolated

### 🔗 Integration Tests (Realistic)  
- **Purpose**: Test full API flows, CQRS integration, and cross-layer functionality
- **Persistence**: Uses `PERSISTENCE_MODE=in-memory` by default
- **Dependencies**: No external services required
- **Speed**: ~9 seconds for 53 tests
- **Coverage**: Full-stack FastAPI endpoint testing

### 🐘 PostgreSQL Integration Tests (Production-Like)
- **Purpose**: Test database persistence, functional mappers, and real database constraints
- **Persistence**: Uses `PERSISTENCE_MODE=postgres`
- **Dependencies**: Requires PostgreSQL via Docker
- **Speed**: Variable (depends on database)
- **Coverage**: Real database persistence and ACID compliance

## Running Tests

### Quick Commands

```bash
# Run unit tests (fast, no dependencies)
make test-unit

# Run integration tests (in-memory, no dependencies)  
make test-integration

# Start PostgreSQL database
make db-up

# Test PostgreSQL integration (requires db-up)
make test-postgres-setup
```

### Detailed Commands

```bash
# Unit tests only
PYTHONPATH=src python -m pytest src/tests/unit/ -v

# Integration tests with in-memory persistence
PERSISTENCE_MODE=in-memory PYTHONPATH=src python -m pytest src/tests/integration/usecases/ src/tests/integration/aux/ -v

# PostgreSQL tests (requires database running)
PERSISTENCE_MODE=postgres PYTHONPATH=src python -m pytest src/tests/integration/ -v --ignore=src/tests/integration/postgres/test_database_persistence.py
```

## Test Results Summary

### ✅ Current Status (All Passing)

| Test Suite | Count | Status | Runtime | Dependencies |
|------------|--------|---------|---------|--------------|
| **Unit Tests** | 87 | ✅ Pass | ~5s | None |
| **Integration Tests** | 53 | ✅ Pass | ~9s | None |  
| **PostgreSQL Core** | Manual | ✅ Pass | ~2s | Docker + PostgreSQL |

**Total: 140 automated tests passing**

### 🎯 Test Coverage

- **Domain Logic**: 87 unit tests covering entities, value objects, events, CQRS
- **API Integration**: 53 integration tests covering all FastAPI endpoints
- **Database Persistence**: PostgreSQL integration verified with functional mappers
- **Authentication Flows**: Complete registration → login → validation → logout cycles
- **Error Handling**: Comprehensive error scenarios and edge cases

## Architecture Verification

### ✅ Functional/OOP Hybrid Confirmed
Our recent refactoring successfully implemented the hybrid functional/OOP architecture:

| Component | Implementation | ✅ Paradigm | Verification |
|-----------|----------------|-------------|--------------|
| **Pure Mappers** | 🟡 Functional | `row_to_user()`, `user_to_db_params()` | Unit + Integration |
| **Repositories** | 🔵 OOP | PostgreSQL classes with state/behavior | PostgreSQL Tests |
| **Value Objects** | 🟡 Functional | Immutable `NamedTuple` + factories | 87 Unit Tests |
| **Use Cases** | 🟡 Functional | Pure async functions | 53 Integration Tests |
| **Entities** | 🔵 OOP | Rich domain models with behavior | 87 Unit Tests |

### ✅ CQRS Separation Verified
- **Command Side** (1% traffic): Registration, login, logout
- **Query Side** (99% traffic): Token validation, health checks, user info
- **Performance Optimized**: Separate read/write repositories with minimal query dependencies

### ✅ Persistence Modes Confirmed
- **In-Memory Mode**: Fast, isolated, perfect for unit/integration tests
- **PostgreSQL Mode**: Production-ready, ACID compliant, real database constraints
- **Dynamic Switching**: Environment variable controls persistence backend
- **Functional Mappers**: Pure functions handle database ↔ domain transformations

## Development Workflow

### 1. **During Development** 
```bash
make test-unit          # Quick feedback (5s)
```

### 2. **Before Commit**
```bash  
make test-unit          # Verify domain logic
make test-integration   # Verify API integration
```

### 3. **Before Deploy**
```bash
make db-up             # Start PostgreSQL
make test-postgres-setup     # Verify database integration
```

### 4. **CI/CD Pipeline**
```bash
make test-unit && make test-integration  # Fast automated tests
# PostgreSQL tests run in containerized CI environment
```

## Troubleshooting

### Unit Tests Failing
- Check `PERSISTENCE_MODE` is not set to `postgres`
- Ensure no external service dependencies
- Run: `PYTHONPATH=src python -m pytest src/tests/unit/ -v`

### Integration Tests Failing
- Verify FastAPI dependency injection works
- Check that `get_auth_functions()` resolves correctly
- Run with explicit persistence: `PERSISTENCE_MODE=in-memory`

### PostgreSQL Tests Failing  
- Ensure PostgreSQL is running: `make db-up`
- Check database connection string in environment
- Verify database initialization completed
- Check Docker container status: `docker-compose ps`

---

**This test architecture ensures fast development cycles while maintaining confidence in production deployments.**