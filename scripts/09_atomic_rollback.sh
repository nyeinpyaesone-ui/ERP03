#!/bin/bash
set -e

# =============================================================================
# STEP 9: ATOMIC ROLLBACK ON FAILURE
# Implements atomic rollback mechanism for failed deployments
# =============================================================================

echo "🔄 Step 9: Atomic Rollback Mechanism"

COMPOSE_FILE="docker-compose.prod.yml"
ROLLBACK_DIR="docker/rollbacks"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Function to perform rollback
perform_rollback() {
    local REASON="$1"
    echo ""
    echo "⚠️  DEPLOYMENT FAILED: $REASON"
    echo "🔄 Initiating atomic rollback..."
    
    # Stop all application services
    echo "🛑 Stopping application services..."
    docker-compose -f "$COMPOSE_FILE" stop erp-backend ai-backend
    
    # Restore previous database backup if exists
    LATEST_BACKUP=$(ls -t "$ROLLBACK_DIR"/db_backup_*.sql 2>/dev/null | head -n1)
    if [ -n "$LATEST_BACKUP" ]; then
        echo "💾 Restoring database from backup: $LATEST_BACKUP"
        cat "$LATEST_BACKUP" | docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U erpuser -d erpdb
        echo "✅ Database restored"
    else
        echo "⚠️  No database backup found, skipping restore"
    fi
    
    # Restart with previous images
    echo "🏗️  Restarting with previous images..."
    docker-compose -f "$COMPOSE_FILE" up -d erp-backend ai-backend
    
    echo ""
    echo "✅ Rollback completed"
    echo "⚠️  Please investigate the failure before retrying deployment"
}

# Check if this is a rollback request
if [ "$1" = "--rollback" ]; then
    perform_rollback "Manual rollback requested"
    exit 0
fi

# Create rollback directory
mkdir -p "$ROLLBACK_DIR"

# Backup current database state before migration
echo "💾 Creating pre-deployment database backup..."
BACKUP_FILE="$ROLLBACK_DIR/db_backup_$TIMESTAMP.sql"

docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U erpuser -d erpdb > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Database backup created: $BACKUP_FILE"
    
    # Keep only last 5 backups
    ls -t "$ROLLBACK_DIR"/db_backup_*.sql | tail -n +6 | xargs -r rm
else
    echo "❌ Failed to create database backup"
    echo "⚠️  Continuing without backup (rollback may not be possible)"
fi

# Save current container state
echo "📦 Saving current container state..."
docker-compose -f "$COMPOSE_FILE" ps > "$ROLLBACK_DIR/state_$TIMESTAMP.txt"

# Tag current images for rollback
echo "🏷️  Tagging current images for rollback..."
for image in erp03/erp-backend:latest erp03/ai-backend:latest; do
    if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "$image"; then
        docker tag "$image" "${image%:latest}:rollback_$TIMESTAMP"
        echo "   Tagged: $image -> ${image%:latest}:rollback_$TIMESTAMP"
    fi
done

# Create rollback script
ROLLBACK_SCRIPT="$ROLLBACK_DIR/rollback_$TIMESTAMP.sh"
cat > "$ROLLBACK_SCRIPT" << 'EOF'
#!/bin/bash
TIMESTAMP="{{TIMESTAMP}}"
COMPOSE_FILE="docker-compose.prod.yml"
ROLLBACK_DIR="docker/rollbacks"

echo "🔄 Rolling back to state before $TIMESTAMP..."

# Stop services
docker-compose -f "$COMPOSE_FILE" stop erp-backend ai-backend

# Restore database
BACKUP_FILE="$ROLLBACK_DIR/db_backup_$TIMESTAMP.sql"
if [ -f "$BACKUP_FILE" ]; then
    cat "$BACKUP_FILE" | docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U erpuser -d erpdb
fi

# Restart with rollback images
docker-compose -f "$COMPOSE_FILE" up -d erp-backend ai-backend

echo "✅ Rollback completed"
EOF

sed -i "s/{{TIMESTAMP}}/$TIMESTAMP/" "$ROLLBACK_SCRIPT"
chmod +x "$ROLLBACK_SCRIPT"

echo "✅ Rollback script created: $ROLLBACK_SCRIPT"
echo ""
echo "📋 Rollback artifacts:"
echo "   - Database backup: $BACKUP_FILE"
echo "   - State snapshot: $ROLLBACK_DIR/state_$TIMESTAMP.txt"
echo "   - Rollback script: $ROLLBACK_SCRIPT"
echo ""
echo "✅ Atomic rollback mechanism ready"
echo ""
echo "To manually rollback, run:"
echo "   $ROLLBACK_SCRIPT"
echo "   or"
echo "   $0 --rollback"
