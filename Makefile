# Heimdall Authentication Service - Development Makefile

.PHONY: help install test test-unit test-integration test-postgres test-all clean build run dev docker-up docker-down

# Default target
help:
	@echo "Heimdall Authentication Service - Available Commands"
	@echo "================================================="
	@echo ""
	@echo "Development:"
	@echo "  install           Install dependencies"
	@echo "  dev               Start development server"
	@echo "  clean             Clean build artifacts and cache"
	@echo ""
	@echo "Testing:"
	@echo "  test              Run unit tests (fast, in-memory)"
	@echo "  test-unit         Run unit tests with in-memory persistence"
	@echo "  test-integration  Run integration tests with in-memory persistence"
	@echo "  test-postgres     Run PostgreSQL integration tests (requires db-up)"
	@echo "  test-postgres-setup  Run PostgreSQL tests with automatic setup"
	@echo "  test-all          Run all test suites"
	@echo ""
	@echo "Docker:"
	@echo "  docker-up         Start services with Docker Compose"
	@echo "  docker-down       Stop Docker services"
	@echo "  docker-test       Run tests in Docker with PostgreSQL"
	@echo "  build             Build Docker images"
	@echo ""

# Development
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements-dev.txt || pip install asyncpg pytest pytest-asyncio httpx faker

dev:
	@echo "🚀 Starting development server..."
	PYTHONPATH=src USE_POSTGRES=false python -m uvicorn heimdall.presentation.api.main:app --reload --host 0.0.0.0 --port 8000

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf dist build test-results htmlcov .coverage coverage.xml 2>/dev/null || true

# Testing
test: test-unit

test-unit:
	@echo "🔬 Running unit tests (in-memory persistence)..."
	PYTHONPATH=src python -m pytest src/tests/unit/ -v --tb=short

test-integration:
	@echo "🔗 Running integration tests (in-memory persistence)..."
	PERSISTENCE_MODE=in-memory PYTHONPATH=src python -m pytest src/tests/integration/usecases/ src/tests/integration/aux/ -v --tb=short

test-postgres:
	@echo "🐘 Running PostgreSQL integration tests..."
	@echo "📋 Prerequisites: Docker running, 'make db-up' executed"
	PERSISTENCE_MODE=postgres PYTHONPATH=src python -m pytest -c pytest-integration.ini --tb=short

test-postgres-setup:
	@echo "🐘 Running PostgreSQL integration tests with setup..."
	./scripts/test-postgres-working.sh

test-all:
	@echo "🧪 Running all test suites..."
	./scripts/run-integration-tests.sh --all

# Docker
docker-up:
	@echo "🐳 Starting Docker services..."
	docker-compose up -d

docker-down:
	@echo "🛑 Stopping Docker services..."
	docker-compose down -v

docker-test:
	@echo "🧪 Running Docker tests..."
	./scripts/run-integration-tests.sh --postgres --verbose

build:
	@echo "🔨 Building Docker images..."
	docker-compose build

# CI/CD helpers
ci-test: clean
	@echo "🏗️ Running CI test suite..."
	./scripts/run-integration-tests.sh --all --verbose

# Quick commands for common development tasks
quick-test: test-unit
	@echo "✅ Quick unit tests completed"

full-test: test-all
	@echo "✅ Full test suite completed"

# Database helpers
db-up:
	@echo "🐘 Starting PostgreSQL only..."
	docker-compose up -d postgres

db-shell:
	@echo "🐚 Opening database shell..."
	docker-compose exec postgres psql -U heimdall_user -d heimdall

# Development helpers  
lint:
	@echo "🔍 Running code linting..."
	PYTHONPATH=src ruff check src/ || echo "⚠️ Install ruff: pip install ruff"

format:
	@echo "🎨 Formatting code..."
	PYTHONPATH=src black src/ || echo "⚠️ Install black: pip install black"

# Documentation
docs:
	@echo "📚 Generating documentation..."
	@echo "API docs available at: http://localhost:8000/docs"
	@echo "ReDoc available at: http://localhost:8000/redoc"