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

### Key Decisions

#### Where We Use Functional Programming
- **Use Cases** - Pure functions that accept `(request, dependencies)` 
- **Business Logic** - Stateless transformations and validations
- **Dependency Injection** - Function composition and partial application

```python
# Example: Functional use case
async def login_user(request: LoginRequest, deps: Dependencies) -> LoginResponse:
    user = await deps.user_repository.find_by_email(email)
    session = user.authenticate(password)
    # ...
```

#### Where We Use OOP
- **Domain Entities** - User, Session (objects with identity and behavior)
- **Value Objects** - Email, Password, Token (immutable domain concepts)
- **Repository Interfaces** - Abstract data access patterns

The reasoning: Entities and Value Objects represent core business concepts that benefit from encapsulation, while use cases are essentially data transformations that work better as pure functions.

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
│   │   ├── entities/    # User, Session
│   │   ├── value_objects/  # Email, Password, Token
│   │   └── repositories/   # Abstract interfaces
│   └── application/     # Use cases & orchestration
│       ├── use_cases/   # Pure business functions
│       └── services/    # Function composition
└── tests/
    └── unit/           # Comprehensive test coverage
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