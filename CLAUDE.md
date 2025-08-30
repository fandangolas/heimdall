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

### Functional vs OOP Strategy
| Component | Approach | Reasoning |
|-----------|----------|-----------|
| **Use Cases** | 🟡 Functional | `async def login_user(request, deps)` - Pure transformations, easier testing |
| **Value Objects** | 🟡 Functional | `Email = NamedTuple(...)` - Immutable data, no identity |
| **Domain Events** | 🟡 Functional | `UserCreated(user_id, email)` - Immutable event data, no behavior needed |
| **DTOs** | 🟡 Functional | `LoginRequest(email, password)` - Pure data containers for boundaries |
| **Entities** | 🔵 OOP | `class User:` - Identity + behavior, natural domain modeling |
| **Services** | 🟡 Functional | Function composition, stateless operations |
| **Repositories** | 🔵 OOP | `class UserRepository:` - Abstract interfaces, familiar patterns |

**Key Insight**: Use functional programming for **data transformations** (use cases, value objects, domain events, DTOs) and OOP for **domain concepts with identity** (entities, repositories).

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

### Phase 2: Read/Write Optimization (Simple CQRS)
**Goal**: Optimize for 100:1 read/write ratio without full CQRS complexity
1. **Separate Handlers**: Different services for commands (writes) and queries (reads)
2. **Redis Caching**: Add caching layer for token validation (first step toward CQRS)
3. **Same Database**: Still using single PostgreSQL, but optimized query patterns
4. **Performance Testing**: Validate sub-10ms response times

### Phase 3: Full CQRS Implementation
**Goal**: Complete separation of read/write models for extreme performance
1. **Separate Models**: Different data models for commands and queries
2. **Event Sourcing**: Store domain events for audit trail
3. **Projections**: Pre-computed read models in Redis
4. **Eventual Consistency**: Handle async updates between write and read sides

### Phase 4: High Availability & Scaling
**Goal**: Production-ready distributed system
1. **Read Replicas**: PostgreSQL read replicas for query side
2. **Redis Cluster**: Distributed caching for high availability
3. **Horizontal Scaling**: Multiple service instances
4. **Circuit Breakers**: Resilience patterns for external dependencies

### Phase 5: Security & Integration
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

## Project Structure (Clean Architecture)
```
heimdall/
├── src/
│   ├── heimdall/
│   │   ├── domain/          # Enterprise Business Rules
│   │   │   ├── entities/   # User, Session, Role
│   │   │   ├── value_objects/ # Token, Permission, Password
│   │   │   ├── events/     # UserLoggedIn, TokenExpired
│   │   │   ├── repositories/ # Repository interfaces
│   │   │   └── services/   # Domain services
│   │   ├── application/    # Application Business Rules
│   │   │   ├── use_cases/  # LoginUseCase, ValidateTokenUseCase
│   │   │   ├── dto/        # Data Transfer Objects
│   │   │   └── interfaces/ # External service interfaces
│   │   ├── infrastructure/ # Frameworks & Drivers
│   │   │   ├── persistence/ # PostgreSQL, Redis implementations
│   │   │   ├── security/   # JWT, encryption implementations
│   │   │   ├── messaging/  # Event bus, message broker
│   │   │   └── config/     # Configuration management
│   │   └── presentation/   # Interface Adapters
│   │       ├── api/        # FastAPI routes
│   │       ├── handlers/   # Request handlers
│   │       └── schemas/    # Pydantic models
│   └── tests/
│       ├── unit/           # Domain & use case tests
│       ├── integration/    # Repository & service tests
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

# When Poetry is set up:
poetry install    # Install dependencies
poetry run pytest # Run tests
poetry run uvicorn heimdall.api.main:app --reload  # Run dev server

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

### Progressive CQRS Adoption
1. **Phase 1**: Same model, different use cases
2. **Phase 2**: Add caching layer for reads
3. **Phase 3**: Separate read/write models
4. **Phase 4**: Full event sourcing and projections

## Testing Strategy
- **Unit Tests**: Core business logic, event handlers
- **Integration Tests**: Database operations, cache operations
- **Load Tests**: Validate performance requirements
- **Security Tests**: Authentication flows, rate limiting

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
- **Add new endpoint**: Create route in `api/`, handler in `commands/` or `queries/`
- **Add domain event**: Define in `core/events.py`, handle in `events/handlers.py`
- **Update projection**: Modify in `projections/`, ensure event replay works
- **Add migration**: Use Alembic for database schema changes
- **Performance optimization**: Profile first, optimize Redis usage, consider batching

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