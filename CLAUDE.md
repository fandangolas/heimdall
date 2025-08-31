# CLAUDE.md - Heimdall Project Assistant Guidelines

## Project Overview
**Heimdall** is a high-performance distributed authentication and authorization system designed for microservices architectures. Named after the Norse guardian of Bifrost Bridge, it serves as the authentication gateway handling extreme loads (1M+ token validations/minute).

## Core Architecture
- **Clean Architecture**: Layered architecture with clear boundaries and dependencies pointing inward
- **Domain-Driven Design (DDD)**: Rich domain models, aggregates, and value objects
- **Hybrid Functional/OOP**: Strategic use of functional programming where it adds value
- **SOLID Principles**: Single responsibility, dependency injection, interface segregation
- **Gradual CQRS Adoption**: Progressive separation of read/write operations as performance needs grow
- **Event-Driven**: Domain events for audit trails and state changes
- **Read-Heavy Optimization**: 100:1 read/write ratio optimization with Redis caching

### Hybrid Functional/OOP Strategy (Completed)
| Component | Approach | Reasoning |
|-----------|----------|-----------|
| **Commands** | 🟡 Functional | `async def login_user_command(request, deps)` - Write operations, pure functions |
| **Queries** | 🟡 Functional | `async def validate_token_query(token, deps)` - Read operations, optimized |
| **Value Objects** | 🟡 Functional | `NamedTuple + factory functions` - Immutable, validated data structures |
| **Domain Events** | 🟡 Functional | `UserCreated(user_id, email) -> DomainEventValue` - Immutable event data |
| **DTOs** | 🟡 Functional | `LoginRequest(email, password) -> LoginRequestValue` - Type-safe boundaries |
| **Dependencies** | 🟡 Functional | `CommandDependencies`, `QueryDependencies` - CQRS separation |
| **Entities** | 🔵 OOP | `class User:` - Identity + behavior, natural domain modeling |
| **Repositories** | 🔵 OOP | `WriteUserRepository`, `ReadSessionRepository` - CQRS interfaces |

**Key Achievement**: Complete functional data layer with CQRS separation for optimal read/write performance. All use cases, value objects, events, and DTOs are now pure functional constructs using NamedTuple + factory functions pattern.

## Technology Stack
- **Language**: Python 3.13.7
- **Framework**: FastAPI with AsyncIO
- **Databases**: PostgreSQL (writes) + Redis Cluster (cache)
- **ORM/Driver**: asyncpg (high-performance async PostgreSQL)
- **Validation**: Pydantic for schemas and validation
- **Package Management**: Poetry
- **Containerization**: Docker + Docker Compose
- **Monitoring**: Prometheus + OpenTelemetry

## Development Milestones (Revised for Progressive Architecture)

### Phase 1: Clean Architecture Foundation with DDD ✅ COMPLETED
**Goal**: Establish solid architectural foundation with SOLID principles
1. **Domain Layer**: Core entities (User, Session), value objects (Email, Password, Token), domain events ✅
2. **Use Cases**: Pure functional use cases (login_user, register_user, validate_token) ✅
3. **Repository Pattern**: Abstract interfaces for data access ✅
4. **Hybrid Functional/OOP**: Complete functional data layer + OOP entities ✅
5. **Comprehensive Testing**: 73 unit tests covering all components ✅

**Status**: All functional/OOP components implemented with full test coverage

### Phase 2: Read/Write Optimization + FastAPI Presentation Layer ✅ COMPLETED
**Goal**: Optimize for 100:1 read/write ratio + complete web API implementation
1. **CQRS Separation**: Complete command/query separation with different dependencies ✅
2. **Functional Interface**: `curry_cqrs_functions()` providing optimal command/query dispatch ✅  
3. **Repository Separation**: ReadSessionRepository (minimal) vs WriteUserRepository (full) ✅
4. **Type-Safe DTOs**: ValidateTokenResponse, LoginResponse, RegisterResponse for boundary safety ✅
5. **FastAPI Presentation Layer**: Complete API routes with dependency injection ✅
6. **Integration Tests**: Restructured by CQRS patterns - /commands vs /queries ✅

**Status**: Complete CQRS + FastAPI implementation with 132 passing tests (87 unit + 45 integration)

### Phase 3: Redis Caching Layer
**Goal**: Sub-10ms token validation performance with distributed caching
1. **Redis Integration**: Distributed cache for token validation queries
2. **Cache Strategy**: Cache-aside pattern with TTL-based invalidation
3. **Performance Optimization**: <10ms p99 response times for token validation
4. **Fallback Strategy**: Graceful degradation when cache unavailable

### Phase 4: Full CQRS with Event Sourcing
**Goal**: Complete separation of read/write models for extreme performance
1. **Separate Models**: Different data models for commands and queries
2. **Event Sourcing**: Store domain events for audit trail
3. **Projections**: Pre-computed read models in Redis
4. **Eventual Consistency**: Handle async updates between write and read sides

### Phase 5: High Availability & Scaling
**Goal**: Production-ready distributed system
1. **Read Replicas**: PostgreSQL read replicas for query side
2. **Redis Cluster**: Distributed caching for high availability
3. **Horizontal Scaling**: Multiple service instances
4. **Circuit Breakers**: Resilience patterns for external dependencies

### Phase 6: Security & Integration
**Goal**: Enterprise-grade security and service integration
1. **Rate Limiting**: Distributed rate limiting with Redis
2. **Audit Logging**: Comprehensive security event logging
3. **Service Integration**: Ratatoskr message broker, API gateway features
4. **Observability**: Full monitoring and management dashboard

## Performance Requirements
- **Token Validation**: <10ms p99 response time
- **Throughput**: 1M+ validations/minute (20k+ RPS)
- **Cache Hit Rate**: >98% on Redis
- **Availability**: 99.9% uptime
- **Memory**: <2GB per instance

## Project Structure (CQRS + Clean Architecture + FastAPI)
```
heimdall/
├── src/
│   ├── heimdall/
│   │   ├── domain/          # Enterprise Business Rules
│   │   │   ├── entities/   # User, Session (OOP with behavior)
│   │   │   ├── value_objects/ # Token, Email, Password (Functional NamedTuple)
│   │   │   ├── events/     # UserCreated, UserLoggedIn (Functional NamedTuple)
│   │   │   ├── repositories/ # CQRS separated interfaces
│   │   │   │   ├── read_repositories.py   # ReadSessionRepository (minimal)
│   │   │   │   └── write_repositories.py  # WriteUserRepository (full)
│   │   │   └── services/   # TokenService, PasswordService
│   │   ├── application/    # Application Business Rules (CQRS)
│   │   │   ├── commands/   # Write operations (1% traffic)
│   │   │   │   └── auth_commands.py # login_user_command, register_user_command
│   │   │   ├── queries/    # Read operations (99% traffic)  
│   │   │   │   └── auth_queries.py  # validate_token_query
│   │   │   ├── cqrs.py    # curry_cqrs_functions() - functional interface
│   │   │   └── dto/        # Type-safe DTOs (Functional NamedTuple)
│   │   ├── infrastructure/ # Frameworks & Drivers
│   │   │   ├── persistence/ # PostgreSQL, Redis implementations
│   │   │   ├── security/   # JWT, encryption implementations
│   │   │   ├── messaging/  # Event bus, message broker
│   │   │   └── config/     # Configuration management
│   │   └── presentation/   # Interface Adapters
│   │       └── api/        # FastAPI Application
│   │           ├── main.py      # FastAPI app configuration
│   │           ├── routes.py    # Authentication endpoints
│   │           ├── dependencies.py # Dependency injection
│   │           ├── schemas.py   # Pydantic request/response schemas
│   │           └── health.py    # Health check endpoints
│   └── tests/
│       ├── unit/           # 87 tests - Domain, commands, queries
│       ├── integration/    # 45 tests - Full-stack API testing
│       │   ├── aux/        # Test infrastructure (HeimdallAPIClient)
│       │   └── usecases/   # Organized by CQRS patterns
│       │       ├── commands/  # Write operation tests (1% traffic)
│       │       └── queries/   # Read operation tests (99% traffic)
│       └── e2e/           # End-to-end API tests
├── docker/
├── migrations/
├── docs/
├── pyproject.toml
└── docker-compose.yml
```

## Development Commands
```bash
# Python is already configured via asdf (3.13.7)
python --version  # Should show Python 3.13.7

# Run tests (current setup)
PYTHONPATH=src python -m pytest src/tests/unit/test_functional_use_cases.py -v  # Unit tests
PYTHONPATH=src python -m pytest src/tests/ -v  # All tests (132 total)

# Run development server (when ready)
poetry install    # Install dependencies
poetry run uvicorn heimdall.presentation.api.main:app --reload --host 0.0.0.0 --port 8000

# API Endpoints (when server running)
curl http://localhost:8000/                    # Service discovery
curl http://localhost:8000/health              # Health check
curl http://localhost:8000/docs                # Swagger UI
curl http://localhost:8000/redoc               # ReDoc documentation

# Docker commands (when configured):
docker-compose up -d     # Start services
docker-compose down     # Stop services
docker-compose logs -f  # View logs
```

## Key Design Patterns & Principles

### Architectural Patterns
1. **Clean Architecture**: Dependency rule - dependencies point inward
2. **Hexagonal Architecture**: Ports and adapters for external services
3. **Repository Pattern**: Abstract data access behind interfaces
4. **Use Case Pattern**: One class per business operation
5. **Dependency Injection**: Constructor injection via FastAPI

### SOLID Principles Applied
- **S**: Each use case handles one business operation
- **O**: New features = new use cases, not modifying existing ones
- **L**: Repository implementations are interchangeable
- **I**: Separate interfaces for read and write repositories
- **D**: Depend on domain interfaces, not infrastructure

### DDD Tactical Patterns
1. **Entities**: Objects with identity (User, Session)
2. **Value Objects**: Immutable objects (Token, Permission)
3. **Aggregates**: Consistency boundaries (User aggregate)
4. **Domain Events**: Capture important state changes
5. **Domain Services**: Complex business logic

### Progressive CQRS Adoption ✅ Phase 2 Complete
1. **Phase 1**: Clean Architecture + DDD foundation ✅
2. **Phase 2**: CQRS separation + FastAPI presentation layer ✅  
3. **Phase 3**: Add Redis caching layer for sub-10ms performance (next)
4. **Phase 4**: Full CQRS with separate read/write models
5. **Phase 5**: Event sourcing and projections
6. **Phase 6**: High availability and scaling

## Testing Strategy (132 Total Tests)
- **Unit Tests**: 87 tests - Core business logic, CQRS commands/queries, domain entities
- **Integration Tests**: 45 tests - Full-stack API testing through FastAPI endpoints
  - **Commands**: Write operations (login, register, logout) - 1% traffic
  - **Queries**: Read operations (token validation, health checks) - 99% traffic
  - **Service Discovery**: API documentation and endpoint discovery
- **Load Tests**: Validate performance requirements (token validation <100ms)
- **Security Tests**: Authentication flows, input validation, rate limiting

## Security Considerations
- JWT tokens with short expiration (15 minutes)
- Rate limiting at multiple levels (IP, user, endpoint)
- Audit logging for all authentication events
- Password policy enforcement
- 2FA support for critical operations
- Request signing for service-to-service auth

## Database Schema Approach
### Write Side (PostgreSQL Master)
- Users table (credentials, metadata)
- Roles and permissions tables
- Events table (event sourcing)
- Sessions table

### Read Side (Redis + PostgreSQL Replicas)
- Cached token validations
- User session projections
- Permission cache projections
- Pre-computed read models

## Integration Points
- **Ratatoskr**: Message broker for event publishing
- **Load Balancer**: Token pre-validation at edge
- **Core Banking Lab**: Batch validation API
- **Monitoring Stack**: Metrics and tracing

## Development Best Practices
1. Always use async/await for I/O operations
2. Implement proper error handling and logging
3. Use type hints throughout the codebase
4. Follow PEP 8 style guidelines
5. Write comprehensive docstrings
6. Maintain high test coverage (>80%)
7. Use environment variables for configuration
8. Never commit secrets or credentials

## Common Tasks
- **Add new command**: Create in `application/commands/auth_commands.py`, add to CommandDependencies if needed
- **Add new query**: Create in `application/queries/auth_queries.py`, optimize for read performance
- **Add domain event**: Define in `domain/events.py` using NamedTuple pattern
- **Add DTO**: Create in `application/dto/` using NamedTuple + factory functions for type safety  
- **Add migration**: Use Alembic for database schema changes
- **Performance optimization**: Profile queries first, consider caching layer, batch operations
- **Update CQRS interface**: Modify `curry_cqrs_functions()` in `application/cqrs.py`

## Monitoring & Debugging
- Health check endpoint: `/health`
- Metrics endpoint: `/metrics` (Prometheus format)
- Structured logging with correlation IDs
- Distributed tracing with OpenTelemetry
- Performance profiling with py-spy

## Important Notes
- This is a defensive security system - focus on authentication and authorization only
- Eventual consistency is acceptable (seconds delay for permission updates)
- Prioritize read performance over write performance
- Cache invalidation is critical for security changes
- Always consider the 100:1 read/write ratio in design decisions

## Recent Updates (August 2024)
- **PostgreSQL Integration**: Added full PostgreSQL support with asyncpg driver for production persistence
- **Dual Persistence Mode**: Environment-based switching between in-memory (development) and PostgreSQL (production)
- **Enhanced Testing**: 143 total tests including PostgreSQL integration tests with Docker support
- **Linting Configuration**: Configured ruff to support PascalCase factory functions while maintaining security rules
- **API Refinement**: `TokenClaims` factory now auto-generates `issued_at` timestamp (removed as parameter)