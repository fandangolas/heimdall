# Heimdall Authentication Service - Development Makefile

.PHONY: help install dev clean test test-unit test-integration test-all lint format compile check quick workflow ci-test docker-up docker-down build docs

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
	@echo "  test              Run all test suites (unit + integration, no Docker)"
	@echo "  test-unit         Run unit tests only (fast, in-memory)"
	@echo "  test-integration  Run integration tests (in-memory, no Docker)"
	@echo "  test-all          Run unit + integration tests (no Docker)"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint              Run code linting (ruff)"
	@echo "  format            Format code (ruff format)"
	@echo "  compile           Type checking and validation (mypy + ruff)"
	@echo "  check             Run lint + compile"
	@echo ""
	@echo "Workflows:"
	@echo "  quick             Quick unit tests (development)"
	@echo "  workflow          Full development workflow (format, lint, compile, tests)"
	@echo "  ci-test           Complete CI workflow (clean + check + all tests)"
	@echo ""
	@echo "Docker:"
	@echo "  docker-up         Start services with Docker Compose"
	@echo "  docker-down       Stop Docker services"
	@echo "  build             Build Docker images"
	@echo ""

# Development
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements-dev.txt || pip install asyncpg pytest pytest-asyncio httpx faker

dev:
	@echo "🚀 Starting development server (in-memory persistence)..."
	PERSISTENCE_MODE=in-memory PYTHONPATH=src python -m uvicorn heimdall.presentation.api.main:app --reload --host 0.0.0.0 --port 8000

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf dist build test-results htmlcov .coverage coverage.xml 2>/dev/null || true

# Testing
test: test-all

test-unit:
	@echo "🔬 Running unit tests (in-memory persistence)..."
	PYTHONPATH=src python -m pytest src/tests/unit/ -v --tb=short

test-integration:
	@echo "🔗 Running integration tests (in-memory persistence)..."
	PERSISTENCE_MODE=in-memory PYTHONPATH=src python -m pytest src/tests/integration/usecases/ src/tests/integration/aux/ -v --tb=short


test-all: test-unit test-integration
	@echo "✅ All test suites completed successfully"

# Docker
docker-up:
	@echo "🐳 Starting Docker services..."
	docker-compose up -d

docker-down:
	@echo "🛑 Stopping Docker services..."
	docker-compose down -v

build:
	@echo "🔨 Building Docker images..."
	docker-compose build

# CI/CD helpers
ci-test: clean compile test-all
	@echo "🏗️ CI test suite completed successfully"

# Development shortcuts  
quick: test-unit
	@echo "✅ Quick unit tests completed"

check: lint compile
	@echo "✅ Code quality checks completed"

# Full development workflow
workflow: clean format lint compile test-unit test-integration
	@echo "🎉 Full development workflow completed successfully!"


# Code Quality
lint:
	@echo "🔍 Running code linting with ruff..."
	@ruff check . || (echo "⚠️ Install ruff: pip install ruff" && exit 1)

format:
	@echo "🎨 Formatting code with ruff..."
	@ruff format . || (echo "⚠️ Install ruff: pip install ruff" && exit 1)

compile:
	@echo "🔧 Type checking and validation..."
	@echo "📝 Running mypy type checking..."
	@PYTHONPATH=src mypy src/heimdall/ --ignore-missing-imports || (echo "⚠️ Install mypy: pip install mypy" && exit 1)
	@echo "🔍 Running ruff linting..."
	@ruff check src/
	@echo "✅ All checks passed!"

# Documentation
docs:
	@echo "📚 Generating documentation..."
	@echo "API docs available at: http://localhost:8000/docs"
	@echo "ReDoc available at: http://localhost:8000/redoc"