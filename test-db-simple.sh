#!/bin/bash
# Simple PostgreSQL test script

set -e

echo "🧪 Testing PostgreSQL setup..."

# Start just PostgreSQL
echo "Starting PostgreSQL..."
docker-compose -f docker-compose.test.yml up -d test-postgres

echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Check if PostgreSQL is healthy
echo "Testing PostgreSQL connection..."
docker-compose -f docker-compose.test.yml exec -T test-postgres pg_isready -U heimdall_test_user -d heimdall_test

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL is working!"
    
    # Test the schema
    echo "Testing schema..."
    docker-compose -f docker-compose.test.yml exec -T test-postgres psql -U heimdall_test_user -d heimdall_test -c "\dt"
    
    echo "✅ Schema is loaded!"
else
    echo "❌ PostgreSQL failed to start"
    docker-compose -f docker-compose.test.yml logs test-postgres
    exit 1
fi

# Cleanup
echo "Cleaning up..."
docker-compose -f docker-compose.test.yml down -v

echo "✅ Simple PostgreSQL test completed successfully!"