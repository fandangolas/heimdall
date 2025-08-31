#!/bin/bash

# Integration test runner script for PostgreSQL-backed tests
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Heimdall PostgreSQL Integration Test Runner${NC}"
echo "=============================================="

# Configuration
COMPOSE_FILE="docker-compose.test.yml"
TEST_RESULTS_DIR="./test-results"
POSTGRES_TEST_PASSWORD="${POSTGRES_TEST_PASSWORD:-heimdall_test_password}"

# Parse command line arguments
RUN_UNIT_TESTS=false
RUN_INTEGRATION_TESTS=true
RUN_POSTGRES_TESTS=true
KEEP_CONTAINERS=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            RUN_UNIT_TESTS=true
            shift
            ;;
        --integration)
            RUN_INTEGRATION_TESTS=true
            shift
            ;;
        --postgres)
            RUN_POSTGRES_TESTS=true
            shift
            ;;
        --all)
            RUN_UNIT_TESTS=true
            RUN_INTEGRATION_TESTS=true
            RUN_POSTGRES_TESTS=true
            shift
            ;;
        --keep)
            KEEP_CONTAINERS=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --unit              Run unit tests only"
            echo "  --integration       Run mock-based integration tests"
            echo "  --postgres          Run PostgreSQL integration tests"
            echo "  --all               Run all test suites"
            echo "  --keep              Keep containers running after tests"
            echo "  --verbose, -v       Verbose output"
            echo "  --help, -h          Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 --postgres       # Run only PostgreSQL tests"
            echo "  $0 --all --verbose  # Run all tests with verbose output"
            echo "  $0 --keep           # Run tests and keep containers for debugging"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Create test results directory
mkdir -p "$TEST_RESULTS_DIR"

# Function to cleanup containers
cleanup() {
    if [ "$KEEP_CONTAINERS" = false ]; then
        echo -e "${YELLOW}🧹 Cleaning up containers...${NC}"
        docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans
    else
        echo -e "${YELLOW}⏸️  Keeping containers running for debugging...${NC}"
        echo "To stop manually: docker-compose -f $COMPOSE_FILE down -v"
    fi
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Export environment variables
export POSTGRES_TEST_PASSWORD

# Start test infrastructure
echo -e "${BLUE}🚀 Starting test infrastructure...${NC}"
docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans
docker-compose -f "$COMPOSE_FILE" build

# Unit tests (if requested)
if [ "$RUN_UNIT_TESTS" = true ]; then
    echo -e "${BLUE}🔬 Running unit tests...${NC}"
    if [ "$VERBOSE" = true ]; then
        docker-compose -f "$COMPOSE_FILE" run --rm heimdall-test \
            pytest src/tests/unit/ -v --tb=short \
            --junitxml=/app/test-results/unit-junit.xml \
            --cov=heimdall --cov-report=xml:/app/test-results/unit-coverage.xml
    else
        docker-compose -f "$COMPOSE_FILE" run --rm heimdall-test \
            pytest src/tests/unit/ --tb=short \
            --junitxml=/app/test-results/unit-junit.xml
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Unit tests passed!${NC}"
    else
        echo -e "${RED}❌ Unit tests failed!${NC}"
        exit 1
    fi
fi

# Mock-based integration tests (if requested)
if [ "$RUN_INTEGRATION_TESTS" = true ]; then
    echo -e "${BLUE}🔗 Running mock-based integration tests...${NC}"
    if [ "$VERBOSE" = true ]; then
        docker-compose -f "$COMPOSE_FILE" run --rm \
            -e USE_POSTGRES=false \
            heimdall-test \
            pytest src/tests/integration/usecases/ -v --tb=short \
            --junitxml=/app/test-results/integration-junit.xml
    else
        docker-compose -f "$COMPOSE_FILE" run --rm \
            -e USE_POSTGRES=false \
            heimdall-test \
            pytest src/tests/integration/usecases/ --tb=short \
            --junitxml=/app/test-results/integration-junit.xml
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Mock integration tests passed!${NC}"
    else
        echo -e "${RED}❌ Mock integration tests failed!${NC}"
        exit 1
    fi
fi

# PostgreSQL integration tests (if requested)
if [ "$RUN_POSTGRES_TESTS" = true ]; then
    echo -e "${BLUE}🐘 Running PostgreSQL integration tests...${NC}"
    
    # Start PostgreSQL and wait for it to be healthy
    docker-compose -f "$COMPOSE_FILE" up -d test-postgres
    
    echo -e "${YELLOW}⏳ Waiting for PostgreSQL to be ready...${NC}"
    timeout 30s bash -c 'until docker-compose -f docker-compose.test.yml exec -T test-postgres pg_isready -U heimdall_test_user -d heimdall_test; do sleep 1; done'
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ PostgreSQL failed to start within timeout${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ PostgreSQL is ready!${NC}"
    
    # Run PostgreSQL-specific tests
    if [ "$VERBOSE" = true ]; then
        docker-compose -f "$COMPOSE_FILE" run --rm heimdall-test \
            pytest src/tests/integration/postgres/ -v --tb=short \
            --junitxml=/app/test-results/postgres-junit.xml \
            --cov=heimdall --cov-report=xml:/app/test-results/postgres-coverage.xml
    else
        docker-compose -f "$COMPOSE_FILE" run --rm heimdall-test \
            pytest src/tests/integration/postgres/ --tb=short \
            --junitxml=/app/test-results/postgres-junit.xml
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PostgreSQL integration tests passed!${NC}"
    else
        echo -e "${RED}❌ PostgreSQL integration tests failed!${NC}"
        exit 1
    fi
fi

# Summary
echo ""
echo -e "${GREEN}🎉 All requested test suites passed successfully!${NC}"
echo ""
echo "Test results available in:"
echo "  📊 JUnit XML: $TEST_RESULTS_DIR/*.xml"
if [ "$VERBOSE" = true ]; then
    echo "  📈 Coverage: $TEST_RESULTS_DIR/*coverage.xml"
fi
echo ""

if [ "$KEEP_CONTAINERS" = true ]; then
    echo -e "${YELLOW}🔍 Containers are still running for debugging:${NC}"
    echo "  Database: localhost:5433"
    echo "  Connect: psql -h localhost -p 5433 -U heimdall_test_user -d heimdall_test"
    echo ""
fi