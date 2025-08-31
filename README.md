# Heimdall 🛡️

A high-performance authentication and authorization system designed for distributed microservices, built with Clean Architecture and functional programming principles.

## Overview

Heimdall (named after the Norse guardian of Bifrost) is an authentication service designed to handle extreme read-heavy workloads typical in banking and financial systems. The project demonstrates a pragmatic blend of functional programming and object-oriented design, optimized for scenarios where token validations vastly outnumber user registrations.

## 📊 Design Rationale

In a typical banking system processing 1,000,000+ operations per minute:
- **99%** are token validations (reads)
- **0.9%** are token refreshes
- **0.1%** are new logins/registrations (writes)

This 1000:1 read/write ratio drove our architectural decisions toward CQRS (Command Query Responsibility Segregation) to optimize for the dominant use case.

## 🏗️ Architecture

### Tech Stack
- **Python 3.13** - Modern Python with native type hints
- **FastAPI + AsyncIO** - High-performance web framework
- **PostgreSQL 16** - Production-grade persistent storage (asyncpg driver)
- **Clean Architecture** - Clear separation of concerns  
- **Domain-Driven Design** - Rich domain models
- **CQRS** - Command Query Responsibility Segregation
- **Functional Programming** - Pure functions for business logic

### Key Decisions: Hybrid Functional/OOP Architecture

We use each paradigm where it's strongest:

| Component | Approach | Reasoning |
|-----------|----------|-----------|
| **Use Cases** | 🟡 Functional | Pure transformations, easier testing |
| **Value Objects** | 🟡 Functional | Immutable data, no identity |
| **Domain Events** | 🟡 Functional | Immutable event data, no behavior needed |
| **DTOs** | 🟡 Functional | Pure data containers for boundaries |
| **Entities** | 🔵 OOP | Identity + behavior, natural domain modeling |
| **Services** | 🟡 Functional | Stateless operations, better composition |
| **Repositories** | 🔵 OOP | Abstract interfaces, familiar patterns |

#### Functional Programming (🟡)
- **Use Cases** - Pure functions: `async def login_user(request, deps) -> response`
- **Value Objects** - Immutable data structures with validation: `NamedTuple + factory functions`
- **Domain Events** - Immutable event data: `UserCreated(user_id, email) -> DomainEventValue`
- **DTOs** - Pure data containers: `LoginRequest(email, password) -> LoginRequestValue`
- **Service Composition** - Function composition and partial application

```python
# Pure function use case
async def login_user(request: LoginRequest, deps: Dependencies) -> LoginResponse:
    user = await deps.user_repository.find_by_email(email)
    session = user.authenticate(password)  # Entity method
    return LoginResponse(access_token=token.value)

# Immutable value object
class EmailValue(NamedTuple):
    value: str
    domain: str

def Email(email_string: str) -> EmailValue:
    # Validation + normalization
    return EmailValue(value=normalized, domain=domain)
```

#### Object-Oriented Programming (🔵)
- **Domain Entities** - Rich objects with identity and behavior
- **Repository Interfaces** - Abstract data access contracts

```python
# Entity with identity and behavior
class User:
    def authenticate(self, password: Password) -> Session:
        if not self.password_hash.verify(password):
            raise ValueError("Invalid credentials")
        return Session.create_for_user(self.id, self.email, self.permissions)
```

This hybrid approach gives us **immutability where it matters** (value objects, use cases) and **rich domain models where appropriate** (entities with business logic).

## 🚀 Progressive Architecture

The project follows a phased approach to CQRS adoption:

1. **Phase 1** ✅ - Clean Architecture foundation with DDD
2. **Phase 2** ✅ - CQRS separation + FastAPI presentation layer + PostgreSQL persistence
3. **Phase 3** - Redis caching layer for sub-10ms performance
4. **Phase 4** - Full CQRS with event sourcing  
5. **Phase 5** - High availability and scaling
6. **Phase 6** - Security, integration, and observability

## 📁 Project Structure

```
src/
├── heimdall/
│   ├── domain/          # Business rules & entities
│   │   ├── entities/    # User, Session (OOP)
│   │   ├── value_objects/  # Email, Password, Token (Functional)
│   │   ├── events/      # Domain events (Functional)
│   │   └── repositories/   # Abstract interfaces (OOP)
│   │       ├── read_repositories.py   # Read-optimized (CQRS)
│   │       └── write_repositories.py  # Write-optimized (CQRS)
│   ├── application/     # Use cases & orchestration
│   │   ├── commands/    # Write operations (CQRS - 1% traffic)
│   │   ├── queries/     # Read operations (CQRS - 99% traffic)
│   │   ├── cqrs.py      # Unified CQRS facade
│   │   ├── dto/         # Data Transfer Objects (Functional)
│   │   └── services/    # Function composition (Functional)
│   ├── infrastructure/ # External integrations
│   │   └── persistence/ # Data persistence layer
│   │       └── postgres/ # PostgreSQL implementation
│   │           ├── database.py        # Connection management
│   │           ├── dependencies.py    # PostgreSQL dependencies
│   │           ├── user_repository.py # User persistence
│   │           └── session_repository.py # Session persistence
│   └── presentation/    # Interface adapters
│       └── api/         # FastAPI application
│           ├── main.py      # FastAPI app configuration
│           ├── routes.py    # Authentication endpoints
│           ├── dependencies.py # Dynamic dependency injection
│           ├── schemas.py   # Pydantic request/response schemas
│           └── health.py    # Health check endpoints
└── tests/
    ├── unit/           # 87 tests - Domain & CQRS logic
    └── integration/    # 56 tests - Full-stack API testing
        ├── aux/        # Test infrastructure (8 tests)
        ├── usecases/   # Organized by CQRS patterns (45 tests)
        │   ├── commands/  # Write operation tests
        │   └── queries/   # Read operation tests
        └── postgres/   # PostgreSQL-specific tests (3 tests)
            ├── test_minimal.py        # Repository functionality
            ├── test_basic_connection.py # Database connectivity
            └── test_database_persistence.py # Advanced scenarios
```

## 🧪 Testing (143 Total Tests)

### Quick Commands (Makefile)
```bash
# Default: Run all test suites (comprehensive, no Docker)
make test              # 140 tests in ~14s (unit + integration)

# Specific test suites
make test-unit         # 87 tests in ~5s (fast feedback)
make test-integration  # 53 tests in ~9s (API integration)
make test-postgres     # 3 tests in ~30s (database persistence, Docker)

# Development workflows
make quick             # Same as test-unit (fast development)
make workflow          # Full development pipeline
make ci-test           # Complete CI validation
```

### Manual Commands
```bash
# Unit tests only
PYTHONPATH=src python -m pytest src/tests/unit/ -v

# Integration tests (in-memory)
PERSISTENCE_MODE=in-memory PYTHONPATH=src python -m pytest src/tests/integration/usecases/ src/tests/integration/aux/ -v

# PostgreSQL tests (requires Docker)
make test-postgres     # Manages Docker lifecycle automatically
```

### Test Coverage
- **87 Unit Tests**: Domain entities, CQRS commands/queries, value objects, events
- **53 Integration Tests**: Full-stack API testing through FastAPI endpoints
  - Commands: Write operations (login, register) - 1% traffic
  - Queries: Read operations (token validation, health checks) - 99% traffic
- **3 PostgreSQL Tests**: Complete database persistence with Docker management
- **Total: 143 automated tests** with comprehensive coverage

## 📖 Documentation

For detailed architectural decisions and trade-offs, see [Technical Assessment](docs/tech_assessment.md).

## 🎯 Design Principles

1. **Optimize for the common case** - Token validation is 99% of traffic
2. **CQRS separation** - Different models for reads vs writes  
3. **Pure functions over classes** - Easier to test, reason about, and scale
4. **Immutable value objects** - Thread-safe by default
5. **Explicit dependencies** - No hidden state or magic
6. **Progressive complexity** - Start simple, evolve as needed
7. **API-first design** - Complete FastAPI integration with type safety
8. **Test-driven architecture** - 132 tests covering all layers

## 🔄 CQRS Implementation (Phase 2 Complete)

### Architecture Overview
Complete command/query separation with FastAPI presentation layer, optimized for the 100:1 read/write ratio typical in authentication systems.

### FastAPI Integration
```python
# FastAPI routes with dependency injection
@router.post("/auth/login")
async def login(
    request: LoginRequestSchema,
    auth_functions: dict = Depends(get_auth_functions)
) -> LoginResponseSchema:
    response = await auth_functions["login"](request.to_domain())
    return LoginResponseSchema.from_domain(response)

@router.post("/auth/validate")
async def validate_token(
    request: ValidateTokenRequestSchema,
    auth_functions: dict = Depends(get_auth_functions)
) -> ValidateTokenResponseSchema:
    response = await auth_functions["validate"](request.token)
    return ValidateTokenResponseSchema.from_domain(response)
```

### Functional CQRS with Curried Functions
```python
# Create optimized dependencies for commands and queries
command_deps = CommandDependencies(user_repo, session_repo, token_service, event_bus)
query_deps = QueryDependencies(cached_session_repo, token_service)  # Minimal deps

# Curry CQRS functions with dependencies baked in
auth_functions = curry_cqrs_functions(command_deps, query_deps)

# Use the curried functions - dependencies already applied
await auth_functions["login"](request)      # Write operation (1% traffic)
await auth_functions["validate"](token)     # Read operation (99% traffic)
```

### Command Side (Write Operations - 1% of traffic)
- **Commands**: `login_user_command`, `register_user_command`, `logout_user_command`
- **Focus**: Data consistency, domain events, full business logic
- **Dependencies**: Write repositories, event bus, full domain services
- **API Endpoints**: `/auth/login`, `/auth/register`, `/auth/logout`

### Query Side (Read Operations - 99% of traffic)  
- **Queries**: `validate_token_query`, `get_user_info_query`
- **Focus**: Performance optimization, minimal dependencies
- **Dependencies**: Read repositories (cacheable), token service only
- **API Endpoints**: `/auth/validate`, `/auth/me`, `/health/*`

### Benefits Achieved
- ✅ **Performance**: Read operations use minimal dependencies
- ✅ **Scalability**: Can scale read/write sides independently  
- ✅ **Functional**: Pure functions with partial application
- ✅ **API Integration**: Complete FastAPI presentation layer
- ✅ **Type Safety**: Pydantic schemas for all request/response boundaries
- ✅ **Maintainability**: Clear separation of concerns
- ✅ **Testing**: 132 tests with full API integration coverage
- ✅ **Evolution**: Ready for Redis caching layer in Phase 3

## 🗄️ PostgreSQL Integration (Phase 2.5 Complete)

### Dual Persistence Architecture
Heimdall supports both in-memory and PostgreSQL persistence modes, controlled by a single environment variable:

```bash
# Use PostgreSQL for production persistence
PERSISTENCE_MODE=postgres

# Use in-memory storage for development/testing  
PERSISTENCE_MODE=in-memory
```

### Dynamic Dependency Injection
The application automatically selects the appropriate repositories based on the persistence mode:

```python
# FastAPI automatically chooses the right backend
def get_auth_functions(
    command_deps: CommandDependencies = Depends(get_dynamic_command_dependencies),
    query_deps: QueryDependencies = Depends(get_dynamic_query_dependencies),
) -> dict[str, Callable]:
    persistence_mode = get_persistence_mode()
    print(f"🔧 Using persistence mode: {persistence_mode}")
    return curry_cqrs_functions(command_deps, query_deps)
```

### PostgreSQL Features
- **Separate CQRS Repositories**: Optimized read/write repository implementations
- **Connection Pooling**: Efficient asyncpg connection management 
- **ACID Compliance**: Full transaction support for data consistency
- **Schema Migrations**: Automated database initialization
- **Docker Integration**: Complete containerized setup with PostgreSQL 16

### Database Schema
```sql
-- Users table with authentication data
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

-- Sessions table for token management
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    email VARCHAR(255) NOT NULL,
    permissions TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);
```

### Configuration
When using PostgreSQL mode, configure the database connection:

```bash
# Required for PERSISTENCE_MODE=postgres
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database
PERSISTENCE_MODE=postgres
```

## 🛠️ Development Setup

### Prerequisites
- Python 3.13.7 (configured via asdf)
- Poetry (for dependency management)
- Docker & Docker Compose (for PostgreSQL database)
- PostgreSQL (for production persistence)
- Redis (for Phase 3 caching layer)

### Quick Start

#### Using Docker (Recommended)
```bash
# Clone and navigate to project
cd heimdall

# Start the full application with PostgreSQL
docker-compose up -d

# Check application status
curl http://localhost:8000/

# View logs
docker-compose logs -f
```

#### Local Development

##### In-Memory Mode (Default)
```bash
# Install dependencies
make install  # or poetry install

# Run all tests to verify setup  
make test     # 140 tests in ~14s (unit + integration)

# Quick development feedback
make quick    # 87 unit tests in ~5s

# Start development server with in-memory storage
make dev      # Starts on localhost:8000

# Code quality checks
make format   # Auto-format code
make lint     # Check code quality  
make compile  # Type checking + validation
```

##### PostgreSQL Mode  
```bash
# Start PostgreSQL with Docker
make db-up    # Start PostgreSQL container only

# Test PostgreSQL integration (manages Docker lifecycle)
make test-postgres  # 3 tests with automatic container management

# Start development server with PostgreSQL persistence  
PERSISTENCE_MODE=postgres make dev

# Database utilities
make db-shell   # Open PostgreSQL shell
make db-up      # Start database only
make db-down    # Stop all services
```

### API Documentation
Once the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health

---

*Part of my portfolio demonstrating Clean Architecture, functional programming, CQRS patterns, and FastAPI integration in Python.*