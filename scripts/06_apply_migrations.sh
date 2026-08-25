#!/bin/bash
set -e

# =============================================================================
# STEP 6: MIGRATION APPLICATION
# Applies database migrations using Alembic
# =============================================================================

echo "🔄 Step 6: Migration Application"

COMPOSE_FILE="docker-compose.prod.yml"
MIGRATION_DIR="ERP-BACKEND/alembic"

# Check if alembic directory exists
if [ ! -d "$MIGRATION_DIR" ]; then
    echo "❌ Alembic migration directory not found: $MIGRATION_DIR"
    exit 1
fi

# Run migrations inside the ERP-BACKEND container
echo "🔧 Applying database migrations..."

docker-compose -f "$COMPOSE_FILE" exec -T erp-backend alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations applied successfully"
else
    echo "❌ Failed to apply migrations"
    exit 1
fi

# Verify migration status
echo ""
echo "📊 Current migration status:"
docker-compose -f "$COMPOSE_FILE" exec -T erp-backend alembic current

echo ""
echo "✅ Migration application completed"
