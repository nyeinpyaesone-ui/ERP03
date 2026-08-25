#!/bin/bash
set -e

# =============================================================================
# STEP 7: SEED DATA LOADING
# Loads initial seed data into the database
# =============================================================================

echo "🌱 Step 7: Seed Data Loading"

COMPOSE_FILE="docker-compose.prod.yml"
SEED_SCRIPT="ERP-BACKEND/scripts/seed_data.py"

# Check if seed script exists
if [ ! -f "$SEED_SCRIPT" ]; then
    echo "❌ Seed script not found: $SEED_SCRIPT"
    exit 1
fi

# Copy seed script to container
echo "📦 Copying seed script to container..."
docker-compose -f "$COMPOSE_FILE" cp "$SEED_SCRIPT" erp-backend:/app/scripts/seed_data.py

# Run seed script inside the ERP-BACKEND container
echo "🔧 Loading seed data..."

docker-compose -f "$COMPOSE_FILE" exec -T erp-backend python /app/scripts/seed_data.py

if [ $? -eq 0 ]; then
    echo "✅ Seed data loaded successfully"
else
    echo "⚠️  Seed data loading had warnings (may already exist)"
fi

echo ""
echo "✅ Seed data loading completed"
