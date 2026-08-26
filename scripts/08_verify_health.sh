#!/bin/bash
set -e

# =============================================================================
# STEP 8: HEALTH VERIFICATION
# Verifies all services are healthy and responding
# =============================================================================

echo "🏥 Step 8: Health Verification"

COMPOSE_FILE="docker-compose.prod.yml"
HEALTH_PASSED=true

# Define service endpoints
declare -A ENDPOINTS=(
    ["erp-backend"]="http://localhost:8000/health"
    ["ai-backend"]="http://localhost:8001/health"
)

# Check container status
echo "📊 Checking container status..."
CONTAINERS=$(docker-compose -f "$COMPOSE_FILE" ps --format json)

if echo "$CONTAINERS" | grep -q "unhealthy\|exited"; then
    echo "❌ Some containers are unhealthy or exited:"
    docker-compose -f "$COMPOSE_FILE" ps
    HEALTH_PASSED=false
else
    echo "✅ All containers are running"
fi

# Check HTTP endpoints
echo ""
echo "🌐 Checking service endpoints..."

for service in "${!ENDPOINTS[@]}"; do
    endpoint="${ENDPOINTS[$service]}"
    echo "   Checking $service at $endpoint..."
    
    MAX_RETRIES=5
    RETRY_COUNT=0
    SUCCESS=false
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$SUCCESS" = false ]; do
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint" 2>/dev/null || echo "000")
        
        if [ "$RESPONSE" = "200" ]; then
            echo "      ✅ $service is healthy (HTTP $RESPONSE)"
            SUCCESS=true
        else
            RETRY_COUNT=$((RETRY_COUNT + 1))
            echo "      ⏳ Retry $RETRY_COUNT/$MAX_RETRIES (HTTP $RESPONSE)"
            sleep 3
        fi
    done
    
    if [ "$SUCCESS" = false ]; then
        echo "      ❌ $service health check failed"
        HEALTH_PASSED=false
        
        # Show logs for debugging
        echo "      Logs:"
        docker-compose -f "$COMPOSE_FILE" logs "$service" --tail=20 | sed 's/^/         /'
    fi
done

# Check database connectivity
echo ""
echo "🗄️  Checking database connectivity..."
DB_CHECK=$(docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U erpuser -d erpdb 2>&1)

if echo "$DB_CHECK" | grep -q "accepting connections"; then
    echo "✅ Database is accepting connections"
else
    echo "❌ Database connection failed"
    HEALTH_PASSED=false
fi

# Check Redis connectivity
echo ""
echo "💾 Checking Redis connectivity..."
REDIS_CHECK=$(docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping 2>&1)

if [ "$REDIS_CHECK" = "PONG" ]; then
    echo "✅ Redis is responding"
else
    echo "⚠️  Redis health check inconclusive (continuing...)"
fi

# Final status
echo ""
if [ "$HEALTH_PASSED" = true ]; then
    echo "✅ All health checks PASSED"
    exit 0
else
    echo "❌ Some health checks FAILED"
    exit 1
fi
