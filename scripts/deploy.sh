#!/bin/bash
set -e

# =============================================================================
# ERP03 COMPLETE DEPLOYMENT PIPELINE
# Executes all 9 deployment steps with automatic rollback on failure
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║           ERP03 DEPLOYMENT PIPELINE                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Starting deployment at $(date)"
echo ""

# Array of deployment steps
STEPS=(
    "01_validate_artifacts.sh:Artifact Validation"
    "02_resolve_environment.sh:Environment Resolution"
    "03_repair_package_structure.sh:Package Structure Repair"
    "04_build_images.sh:Image Building"
    "05_start_infrastructure.sh:Infrastructure Startup"
    "06_apply_migrations.sh:Migration Application"
    "07_load_seed_data.sh:Seed Data Loading"
    "08_verify_health.sh:Health Verification"
    "09_atomic_rollback.sh:Atomic Rollback Setup"
)

DEPLOYMENT_SUCCESS=true
FAILED_STEP=""

# Execute each step
for i in "${!STEPS[@]}"; do
    STEP_INFO="${STEPS[$i]}"
    STEP_FILE="${STEP_INFO%%:*}"
    STEP_NAME="${STEP_INFO##*:}"
    STEP_NUM=$((i + 1))
    
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║  Step $STEP_NUM/9: $STEP_NAME"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    
    if [ ! -f "$SCRIPT_DIR/$STEP_FILE" ]; then
        echo "❌ Step script not found: $STEP_FILE"
        DEPLOYMENT_SUCCESS=false
        FAILED_STEP="$STEP_NAME"
        break
    fi
    
    # Make script executable
    chmod +x "$SCRIPT_DIR/$STEP_FILE"
    
    # Execute step
    if ! "$SCRIPT_DIR/$STEP_FILE"; then
        echo ""
        echo "❌ Step $STEP_NUM failed: $STEP_NAME"
        DEPLOYMENT_SUCCESS=false
        FAILED_STEP="$STEP_NAME"
        break
    fi
    
    echo ""
    echo "✅ Step $STEP_NUM completed: $STEP_NAME"
    echo ""
done

# Handle failure with rollback
if [ "$DEPLOYMENT_SUCCESS" = false ]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║              ⚠️  DEPLOYMENT FAILED                        ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "Failed at step: $FAILED_STEP"
    echo ""
    
    # Ask for rollback
    read -p "Do you want to perform atomic rollback? (y/n): " -n 1 -r ROLLBACK_CONFIRM
    echo ""
    
    if [[ $ROLLBACK_CONFIRM =~ ^[Yy]$ ]]; then
        echo "🔄 Initiating rollback..."
        "$SCRIPT_DIR/09_atomic_rollback.sh" --rollback
    else
        echo "⚠️  Rollback skipped. Manual intervention may be required."
    fi
    
    exit 1
fi

# Deployment successful
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              ✅ DEPLOYMENT SUCCESSFUL                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "All 9 steps completed successfully!"
echo ""
echo "Services available at:"
echo "  - ERP Backend:  http://localhost:8000"
echo "  - AI Backend:   http://localhost:8001"
echo "  - Frontend MRP: http://localhost:3000"
echo ""
echo "Next steps:"
echo "  1. Verify services: ./scripts/08_verify_health.sh"
echo "  2. Access admin panel: http://localhost:3000/admin"
echo "  3. Default credentials: admin / admin123"
echo ""
echo "Deployment completed at $(date)"
