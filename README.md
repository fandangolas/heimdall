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
- **Clean Architecture** - Clear separation of concerns
- **Domain-Driven Design** - Rich domain models
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

1. **Phase 1** ✅ - Clean Architecture foundation
2. **Phase 2** 🔄 - Read/Write model separation
3. **Phase 3** - Event sourcing for audit trails
4. **Phase 4** - Distributed caching (Redis)
5. **Phase 5** - Full CQRS with event streaming

## 📁 Project Structure

```
src/
├── heimdall/
│   ├── domain/          # Business rules & entities
│   │   ├── entities/    # User, Session (OOP)
│   │   ├── value_objects/  # Email, Password, Token (Functional)
│   │   ├── events/      # Domain events (Functional)
│   │   └── repositories/   # Abstract interfaces (OOP)
│   └── application/     # Use cases & orchestration
│       ├── dto/         # Data Transfer Objects (Functional)
│       ├── use_cases/   # Pure business functions (Functional)
│       └── services/    # Function composition (Functional)
└── tests/
    └── unit/           # Comprehensive test coverage (73 tests)
```

## 🧪 Testing

```bash
# Run all tests
PYTHONPATH=src python -m pytest

# Run with coverage
PYTHONPATH=src python -m pytest --cov=heimdall
```

## 📖 Documentation

For detailed architectural decisions and trade-offs, see [Technical Assessment](docs/tech_assessment.md).

## 🎯 Design Principles

1. **Optimize for the common case** - Token validation is 99% of traffic
2. **Pure functions over classes** - Easier to test, reason about, and scale
3. **Immutable value objects** - Thread-safe by default
4. **Explicit dependencies** - No hidden state or magic
5. **Progressive complexity** - Start simple, evolve as needed

---

*Part of my portfolio demonstrating Clean Architecture, functional programming, and CQRS patterns in Python.*