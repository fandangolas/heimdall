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
2. **Phase 2** ✅ - CQRS separation + FastAPI presentation layer
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
│   └── presentation/    # Interface adapters
│       └── api/         # FastAPI application
│           ├── main.py      # FastAPI app configuration
│           ├── routes.py    # Authentication endpoints
│           ├── dependencies.py # Dependency injection
│           ├── schemas.py   # Pydantic request/response schemas
│           └── health.py    # Health check endpoints
└── tests/
    ├── unit/           # 87 tests - Domain & CQRS logic
    └── integration/    # 45 tests - Full-stack API testing
        ├── aux/        # Test infrastructure
        └── usecases/   # Organized by CQRS patterns
            ├── commands/  # Write operation tests
            └── queries/   # Read operation tests
```

## 🧪 Testing (132 Total Tests)

```bash
# Run all tests
PYTHONPATH=src python -m pytest src/tests/ -v

# Run unit tests only (87 tests)
PYTHONPATH=src python -m pytest src/tests/unit/ -v

# Run integration tests only (45 tests)
PYTHONPATH=src python -m pytest src/tests/integration/ -v

# Run with coverage
PYTHONPATH=src python -m pytest --cov=heimdall
```

### Test Coverage
- **87 Unit Tests**: Domain entities, CQRS commands/queries, value objects, events
- **45 Integration Tests**: Full-stack API testing through FastAPI endpoints
  - Commands: Write operations (login, register) - 1% traffic
  - Queries: Read operations (token validation, health checks) - 99% traffic

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

## 🛠️ Development Setup

### Prerequisites
- Python 3.13.7 (configured via asdf)
- Poetry (for dependency management when ready)
- PostgreSQL (for production persistence)
- Redis (for Phase 3 caching layer)

### Quick Start
```bash
# Clone and navigate to project
cd heimdall

# Run all tests to verify setup
PYTHONPATH=src python -m pytest src/tests/ -v

# Run specific functional use case tests
PYTHONPATH=src python -m pytest src/tests/unit/test_functional_use_cases.py -v

# Start development server (when Poetry configured)
poetry run uvicorn heimdall.presentation.api.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
Once the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health

---

*Part of my portfolio demonstrating Clean Architecture, functional programming, CQRS patterns, and FastAPI integration in Python.*