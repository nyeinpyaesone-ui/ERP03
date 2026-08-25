#!/bin/bash
set -e

# =============================================================================
# STEP 5: INFRASTRUCTURE STARTUP
# Starts all infrastructure services using Docker Compose
# =============================================================================

echo "🚀 Step 5: Infrastructure Startup"

COMPOSE_FILE="docker-compose.prod.yml"

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Docker Compose file not found: $COMPOSE_FILE"
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true

# Start infrastructure services (database, redis, etc.)
echo "🏗️  Starting infrastructure services..."
docker-compose -f "$COMPOSE_FILE" up -d postgres redis

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

until docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U erpuser -d erpdb > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ PostgreSQL failed to start within timeout"
        docker-compose -f "$COMPOSE_FILE" logs postgres
        exit 1
    fi
    echo "   Waiting... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo "✅ PostgreSQL is ready"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
sleep 3
if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis health check failed (continuing...)"
fi

# Start application services
echo "🏗️  Starting application services..."
docker-compose -f "$COMPOSE_FILE" up -d erp-backend ai-backend

# Wait for services to initialize
echo "⏳ Waiting for services to initialize..."
sleep 10

# Show running containers
echo ""
echo "📊 Running containers:"
docker-compose -f "$COMPOSE_FILE" ps

echo ""
echo "✅ Infrastructure startup completed"
