#!/bin/bash

# Local test runner - runs tests without Docker for faster development
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Heimdall Local Test Runner${NC}"
echo "============================="

# Check if required dependencies are available
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python not found${NC}"
    exit 1
fi

if ! python -c "import asyncpg" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  asyncpg not found - installing...${NC}"
    pip install asyncpg
fi

# Set environment variables for local testing
export PYTHONPATH="$(pwd)/src"
export USE_POSTGRES=false  # Use mock repositories for local testing

# Parse command line arguments
TEST_SUITE="unit"  # Default to unit tests

case "${1:-}" in
    "unit")
        TEST_SUITE="unit"
        ;;
    "integration")
        TEST_SUITE="integration"
        ;;
    "all")
        TEST_SUITE="all"
        ;;
    *)
        echo "Usage: $0 [unit|integration|all]"
        echo ""
        echo "Examples:"
        echo "  $0 unit        # Run unit tests (fast)"
        echo "  $0 integration # Run integration tests with mocks"
        echo "  $0 all         # Run all tests"
        exit 1
        ;;
esac

# Run tests based on selected suite
case "$TEST_SUITE" in
    "unit")
        echo -e "${BLUE}🔬 Running unit tests...${NC}"
        python -m pytest src/tests/unit/ -v
        ;;
    "integration")
        echo -e "${BLUE}🔗 Running integration tests (with mocks)...${NC}"
        python -m pytest src/tests/integration/usecases/ -v
        ;;
    "all")
        echo -e "${BLUE}🔬 Running unit tests...${NC}"
        python -m pytest src/tests/unit/ -v
        
        echo -e "${BLUE}🔗 Running integration tests (with mocks)...${NC}"
        python -m pytest src/tests/integration/usecases/ -v
        ;;
esac

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi