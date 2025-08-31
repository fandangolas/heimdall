# Heimdall - Tech Assessment & Architectural Decisions

**Project**: Heimdall - Distributed Authentication & Authorization System  
**Theme**: Norse Mythology (Guardian of Bifrost Bridge)  
**Context**: High-performance auth system for microservices ecosystem  
**Target Load**: 1M token validations/minute, 10k concurrent users  

## Project Overview

Heimdall serves as the authentication and authorization gateway for a distributed microservices architecture, specifically designed to handle the authentication needs of high-throughput systems like our Core Banking Lab simulation.

**Key Requirements:**
- Handle 1M+ token validations per minute
- Sub-10ms response time for token validation
- 99.9% uptime with no single point of failure
- Seamless integration with existing services (Ratatoskr message broker, load balancer)

## Architectural Evolution Strategy

This project follows a **progressive architecture approach**, starting with solid foundations and evolving toward CQRS as performance demands grow:

1. **Phase 1**: Clean Architecture + DDD + SOLID principles (solid foundation)
2. **Phase 2**: Simple read/write separation with caching (performance optimization)
3. **Phase 3**: Full CQRS with separate models (extreme performance)
4. **Phase 4**: High availability and scaling (production readiness)
5. **Phase 5**: Security, integration, and observability (enterprise features)

This approach allows the team to:
- Start with familiar patterns and principles
- Learn and adapt gradually
- Only add complexity when justified by requirements
- Maintain clean, testable code throughout

---

## Milestone 1: Clean Architecture Foundation with DDD ✅ COMPLETED
**Duration**: Foundation phase  
**Goal**: Establish solid architectural foundation using Clean Architecture, SOLID principles, and Domain-Driven Design

**Status**: Complete functional/OOP hybrid architecture with comprehensive test coverage (95 tests passing)

### Milestone Details
Build a robust foundation using Clean Architecture layers with clear boundaries, rich domain models, and dependency injection. This phase focuses on creating a maintainable, testable codebase that can evolve toward CQRS as performance needs demand.

**Load Pattern Analysis:**
- Commands: ~10k login operations/minute (write-heavy, complex validation)
- Queries: ~1M token validations/minute (read-heavy, sub-10ms requirement)
- Ratio: 100:1 queries to commands

### Architectural Decisions

**Clean Architecture Layers:**
```python
# Domain Layer - Enterprise Business Rules (no external dependencies)
@dataclass
class User:  # Entity
    id: UserId
    email: Email
    password_hash: PasswordHash
    
    def authenticate(self, password: Password) -> Result[Session]:
        # Pure business logic, no frameworks
        pass

# Application Layer - Use Cases (orchestration)
class LoginUseCase:
    def __init__(self, 
                 user_repo: UserRepository,  # Interface from domain
                 token_service: TokenService,  # Interface from domain
                 event_bus: EventBus):  # Interface from domain
        self.user_repo = user_repo
        self.token_service = token_service
        self.event_bus = event_bus
    
    async def execute(self, request: LoginRequest) -> Result[LoginResponse]:
        # Orchestrate domain objects and services
        user = await self.user_repo.find_by_email(request.email)
        session = user.authenticate(request.password)
        token = self.token_service.generate(session)
        await self.event_bus.publish(UserLoggedIn(user.id, session.id))
        return LoginResponse(token=token)

# Infrastructure Layer - Frameworks & External Services
class PostgreSQLUserRepository(UserRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def find_by_email(self, email: Email) -> Optional[User]:
        # Actual database implementation
        pass

# Presentation Layer - FastAPI
@router.post("/auth/login")
async def login(
    request: LoginRequestSchema,
    use_case: LoginUseCase = Depends(get_login_use_case)
):
    result = await use_case.execute(request.to_domain())
    return result.to_response()
```

**Tech Stack:**
- **FastAPI + AsyncIO**: Command/Query API separation
- **asyncpg**: High-performance PostgreSQL async driver
- **Redis Cluster**: Query-side cache + command-side event publishing
- **Pydantic**: Request/response validation and event schemas
- **Poetry**: Dependency management and packaging

**Domain-Driven Design Patterns:**
```python
# Value Objects - Immutable, no identity
@dataclass(frozen=True)
class Email:
    value: str
    
    def __post_init__(self):
        if not self._is_valid(self.value):
            raise ValueError("Invalid email format")

@dataclass(frozen=True)
class Token:
    value: str
    expires_at: datetime
    
# Domain Events
@dataclass
class UserLoggedIn(DomainEvent):
    user_id: UserId
    session_id: SessionId
    occurred_at: datetime = field(default_factory=datetime.utcnow)

# Aggregates - Consistency boundaries
class UserAggregate:
    def __init__(self, user: User):
        self._user = user
        self._events: List[DomainEvent] = []
    
    def login(self, password: Password) -> Session:
        session = self._user.authenticate(password)
        self._events.append(UserLoggedIn(self._user.id, session.id))
        return session
    
    def get_uncommitted_events(self) -> List[DomainEvent]:
        return self._events.copy()
```

**Database Architecture (Phase 1):**
```
Single PostgreSQL Instance:
  - Users table: Authentication data
  - Sessions table: Active sessions
  - Roles/Permissions: Authorization data
  - Events table: Audit trail
  
Future optimization path:
  Phase 2: Add Redis caching
  Phase 3: Separate read/write models
  Phase 4: Read replicas + Redis cluster
```

**JWT Strategy:**
- Simple JWT implementation initially
- Short-lived access tokens (15 minutes)
- Refresh token rotation
- Stateless validation (no DB hit for valid tokens)

### Open Questions
- Which dependency injection framework to use with FastAPI?
- How to structure domain events for future CQRS migration?
- Should we use ABC (Abstract Base Classes) or Protocols for interfaces?
- Testing strategy for domain logic vs infrastructure?
- How to handle database migrations with clean architecture?

### Concerns
- **Learning Curve**: Team needs to understand Clean Architecture principles
- **Initial Overhead**: More boilerplate code initially
- **Performance**: Extra abstraction layers might add latency
- **Dependency Management**: Careful management of layer dependencies
- **Migration Path**: Ensuring smooth transition to CQRS when needed

---

## Milestone 2: Read/Write Optimization + FastAPI Presentation Layer ✅ COMPLETED  
**Duration**: Optimization + API phase  
**Goal**: Optimize for 100:1 read/write ratio + complete web API implementation

**Status**: Complete CQRS command/query separation, FastAPI presentation layer, and restructured integration tests

### Milestone Details
✅ **Completed**: 
- **CQRS Architecture**: Full command/query separation with commands handling writes (1% traffic) and queries optimized for reads (99% traffic)
- **Functional Interface**: `curry_cqrs_functions()` provides optimal dispatch with dependencies baked in
- **Repository Separation**: ReadSessionRepository (minimal) vs WriteUserRepository/WriteSessionRepository (full)
- **Type-Safe DTOs**: All DTOs use NamedTuple pattern (LoginResponse, ValidateTokenResponse, RegisterResponse)
- **FastAPI Presentation Layer**: Complete web API with authentication endpoints, health checks, and service discovery
- **Integration Tests**: Restructured by CQRS patterns - /commands vs /queries with full API endpoint testing
- **Test Coverage**: 132 total tests (87 unit + 45 integration) all passing

**Next Phase**: Add Redis caching layer to achieve sub-10ms response times for token validation queries.

### Architectural Decisions

**✅ Completed CQRS + FastAPI Implementation:**
```python
# FastAPI Routes with Dependency Injection
@router.post("/auth/login")
async def login(
    request: LoginRequestSchema,
    auth_functions: dict[str, Callable[..., Any]] = Depends(get_auth_functions),
) -> LoginResponseSchema:
    login_request = LoginRequest(email=request.email, password=request.password)
    response = await auth_functions["login"](login_request)
    return LoginResponseSchema(access_token=response.access_token, token_type="bearer")

@router.post("/auth/validate")
async def validate_token(
    request: ValidateTokenRequestSchema,
    auth_functions: dict[str, Callable[..., Any]] = Depends(get_auth_functions),
) -> ValidateTokenResponseSchema:
    token = Token(value=request.token)
    response = await auth_functions["validate"](token)
    return ValidateTokenResponseSchema(
        is_valid=response.is_valid,
        user_id=response.user_id,
        email=response.email,
        permissions=response.permissions,
        error=response.error,
    )

# Command Functions - Optimized for writes (1% traffic) 
async def login_user_command(
    request: LoginRequest, 
    deps: CommandDependencies
) -> LoginResponse:
    # Full context: user_repo, session_repo, token_service, event_bus
    user = await deps.user_repository.find_by_email(request.email)
    session = user.authenticate(request.password)
    token = deps.token_service.generate_token(session)
    await deps.event_bus.publish(UserLoggedIn(user.id))
    return LoginResponse(access_token=token.value)

# Query Functions - Optimized for reads (99% traffic)
async def validate_token_query(
    token: Token, 
    deps: QueryDependencies
) -> ValidateTokenResponse:
    # Minimal deps: session_repo, token_service only
    claims = deps.token_service.validate_token(token)
    session = await deps.session_repository.find_by_id(claims.session_id)
    return ValidateTokenResponse(is_valid=session.is_valid())

# Functional Interface with Curry Pattern
auth_functions = curry_cqrs_functions(command_deps, query_deps)
response = await auth_functions["validate"](token)  # Optimized dispatch
```

**✅ Architecture Achievements:**
- **CQRS Separation**: Commands (1% traffic) vs Queries (99% traffic) with different dependency contexts
- **Functional Interface**: `curry_cqrs_functions()` provides optimal dispatch to correct handler
- **Repository Separation**: ReadSessionRepository (minimal interface) vs WriteUserRepository (full interface)  
- **Type Safety**: All DTOs use NamedTuple pattern - LoginResponse, ValidateTokenResponse, RegisterResponse
- **FastAPI Integration**: Complete presentation layer with dependency injection connecting to CQRS backend
- **Pydantic Schemas**: Type-safe request/response boundaries for all API endpoints
- **Health Checks**: Comprehensive health monitoring with /health, /ready, /live endpoints
- **Service Discovery**: Root endpoint with API documentation and endpoint discovery
- **Test Architecture**: 132 total tests (87 unit + 45 integration) with full API endpoint coverage
- **Integration Test Structure**: Organized by CQRS patterns - /commands vs /queries with proper test isolation

**🎯 Next Phase**: Add Redis caching layer for sub-10ms token validation performance

### FastAPI Endpoints Implemented
```
Authentication Endpoints:
- POST /auth/login      # User login (command - 1% traffic)
- POST /auth/register   # User registration (command - 1% traffic) 
- POST /auth/validate   # Token validation (query - 99% traffic)
- GET  /auth/me         # User info (query - 99% traffic)

Health & Discovery:
- GET  /               # Service discovery and API information
- GET  /health         # Basic health check
- GET  /health/detailed # Detailed system health
- GET  /ready          # Kubernetes readiness probe
- GET  /live           # Kubernetes liveness probe
- GET  /docs           # Swagger UI documentation
- GET  /redoc          # ReDoc documentation
- GET  /openapi.json   # OpenAPI schema
```

### Open Questions for Phase 3 (Redis Caching)
- Cache invalidation strategy for permission changes?
- Optimal cache key structure for fast lookups?
- Should we implement read-through or cache-aside pattern?
- Redis Cluster configuration for high availability?
- Cache warming strategy for new deployments?

### Concerns for Phase 3
- Cache coherency during updates
- Additional complexity in cache management
- Memory requirements for Redis
- Fallback strategy when cache is unavailable
- Performance impact of cache misses during high load

---

## Milestone 3: Redis Caching Layer
**Duration**: Performance optimization phase  
**Goal**: Sub-10ms token validation with distributed caching

### Milestone Details
Implement Redis caching layer specifically for the token validation query (99% of traffic). Focus on achieving sub-10ms p99 response times while maintaining the existing CQRS architecture. This phase adds caching without changing the fundamental command/query separation.

### Architectural Decisions

**Cache Strategy:**
```python
# Cache-Aside Pattern for Token Validation
async def validate_token_query_cached(
    token: Token, 
    deps: QueryDependencies
) -> ValidateTokenResponse:
    # Try cache first
    cache_key = f"token:{token.hash()}"
    cached_result = await deps.redis_client.get(cache_key)
    
    if cached_result:
        return ValidateTokenResponse.from_cache(cached_result)
    
    # Cache miss - query database
    result = await validate_token_query(token, deps)
    
    # Store in cache with TTL
    if result.is_valid:
        await deps.redis_client.setex(cache_key, 300, result.to_cache())
    
    return result
```

**Redis Configuration:**
```yaml
Redis Setup:
  - Single Redis instance initially
  - TTL-based cache expiration (5 minutes)
  - Token validation caching only
  - Fallback to PostgreSQL on cache miss
  
Cache Keys:
  - token:{token_hash} -> ValidateTokenResponse
  - user_sessions:{user_id} -> List[SessionInfo] (future)
```

**Performance Targets:**
- Token validation: <10ms p99 (vs current ~50-100ms)
- Cache hit rate: >95% in steady state
- Fallback latency: <100ms when cache unavailable

### Open Questions
- Redis persistence configuration (RDB vs AOF)?
- Cache warming strategy on deployment?
- Token invalidation on logout/permission changes?

### Concerns
- Additional infrastructure complexity
- Cache coherency with user permission updates
- Redis memory usage growth over time

---

## Milestone 4: Full CQRS Implementation
**Duration**: Advanced optimization phase  
**Goal**: Complete separation of read/write models for extreme performance

### Milestone Details
Evolve the architecture to full CQRS with separate data models for commands and queries. Implement event sourcing for audit trails and introduce projections for pre-computed read models. This phase is triggered when Redis caching + current architecture no longer meets extreme performance requirements.

### Architectural Decisions

**Separate Read/Write Models:**
```python
# Write Model - Optimized for consistency
class UserWriteModel:
    id: UserId
    email: Email
    password_hash: PasswordHash
    created_at: datetime
    updated_at: datetime

# Read Model - Optimized for queries
class UserReadModel:
    user_id: str
    email: str
    permissions: List[str]
    active_sessions: List[SessionInfo]
    last_login: datetime
    
# Projection - Pre-computed for performance
class TokenValidationProjection:
    token_hash: str
    user_id: str
    permissions: Set[str]
    expires_at: datetime
```

**Event Sourcing:**
- Store all state changes as events
- Rebuild projections from event stream
- Event store in PostgreSQL initially
- Consider EventStore DB for scale

**Eventual Consistency:**
- Accept delay between write and read models
- Use domain events to synchronize
- Implement saga pattern for complex flows

### Open Questions
- How long is acceptable eventual consistency delay?
- Event store technology for production scale?
- Projection rebuild strategy during schema changes?

### Concerns
- Complexity of maintaining two models
- Eventual consistency confusion for developers
- Event store growth and archival strategy
- Debugging across separated models

---

## Milestone 5: High Availability & Scaling
**Duration**: Production readiness phase  
**Goal**: Multi-instance deployment with high availability

### Milestone Details
Transform the optimized auth service into a horizontally scalable, highly available system. Add read replicas, implement Redis Cluster for cache distribution, and ensure zero-downtime deployments.

### Architectural Decisions

**Infrastructure Scaling:**
```yaml
Database Layer:
  - PostgreSQL Master: Writes only
  - Read Replicas (3+): Load balanced reads
  - Connection Pooling: PgBouncer
  
Cache Layer:
  - Redis Cluster: Distributed cache
  - Auto-failover: Redis Sentinel
  - Sharding: Consistent hashing
  
Application Layer:
  - Multiple instances: Horizontal scaling
  - Load balancer: Round-robin + health checks
  - Stateless design: Any instance can handle any request
```

**High Availability Patterns:**
- Circuit breakers for external dependencies
- Graceful degradation when cache unavailable
- Health checks and auto-recovery
- Blue-green deployments

**Performance Optimizations:**
- Connection pooling at all layers
- Async/await throughout
- Batch operations where possible
- Resource limits and timeouts

### Open Questions
- Kubernetes vs Docker Swarm for orchestration?
- Active-active vs active-passive database setup?
- Geographic distribution requirements?

### Concerns
- Increased infrastructure complexity
- Higher operational overhead
- Cost of multiple instances and replicas
- Network latency between components

---

## Milestone 6: Security, Integration & Observability
**Duration**: Enterprise features phase  
**Goal**: Production-grade security, service integration, and complete observability

### Milestone Details
Implement comprehensive security measures including rate limiting and audit logging. Build integration capabilities for the microservices ecosystem, and add full observability with monitoring, tracing, and management dashboard.

### Architectural Decisions

**Security Features:**
```python
# Rate Limiting
- Sliding window algorithm in Redis
- Multi-tier: IP, user, endpoint
- Graceful degradation under attack

# Audit & Compliance
- Comprehensive audit logging
- GDPR compliance features
- Security event monitoring
- Anomaly detection
```

**Service Integration:**
```yaml
Ratatoskr: Event publishing for auth events
Load Balancer: Token pre-validation
Core Banking: Batch validation API
External Services: OAuth2, SAML support
```

**Observability Stack:**
```yaml
Metrics: Prometheus + FastAPI metrics
Logs: Structured JSON with correlation IDs
Tracing: OpenTelemetry distributed tracing
Dashboard: Admin UI for management
Alerting: Critical auth event notifications
```

### Open Questions
- Build vs buy for admin dashboard?
- Which OAuth2/SAML libraries to use?
- Audit log retention requirements?

### Concerns
- Security of the management interface itself
- Performance impact of comprehensive logging
- Integration complexity with external identity providers
- Maintaining backward compatibility

---

## Technology Decisions Summary

| Component | Technology | Reasoning |
|-----------|------------|-----------|
| API Framework | FastAPI | Async support, automatic OpenAPI, high performance |
| Database | PostgreSQL | ACID compliance, mature ecosystem, replication |
| Cache | Redis Cluster | High performance, distributed, persistence options |
| Message Queue | Integration with Ratatoskr | Ecosystem consistency |
| Monitoring | Prometheus + OpenTelemetry | Industry standard, rich ecosystem |
| Containerization | Docker + Docker Compose | Development consistency, easy deployment |

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Token Validation | <10ms p99 | Response time |
| Cache Hit Rate | >98% | Redis metrics |
| Throughput | 20k+ RPS | Concurrent validations |
| Availability | 99.9% | Uptime monitoring |
| Memory Usage | <2GB per instance | Runtime metrics |

## Risk Mitigation

**High Impact Risks:**
1. **Redis Cluster Failure**: Fallback to PostgreSQL with circuit breaker
2. **Database Connection Exhaustion**: Connection pooling + queue management
3. **Memory Leaks**: Regular health checks + automatic restarts
4. **Security Vulnerabilities**: Regular dependency updates + security scanning

**Medium Impact Risks:**
1. **Network Partitions**: Graceful degradation modes
2. **Load Spikes**: Auto-scaling capabilities + rate limiting
3. **Configuration Errors**: Validation + gradual rollouts