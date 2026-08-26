#!/bin/bash
set -e

# =============================================================================
# STEP 4: IMAGE BUILDING
# Builds Docker images for all services
# =============================================================================

echo "🐳 Step 4: Image Building"

BUILD_DIR="docker/builds"
mkdir -p "$BUILD_DIR"

# Build ERP-BACKEND image
echo "🏗️  Building ERP-BACKEND image..."
docker build \
    -f ERP-BACKEND/Dockerfile \
    -t erp03/erp-backend:latest \
    --build-arg ENV=production \
    ERP-BACKEND/

if [ $? -eq 0 ]; then
    echo "✅ ERP-BACKEND image built successfully"
else
    echo "❌ Failed to build ERP-BACKEND image"
    exit 1
fi

# Build AI-BACKEND image
echo "🏗️  Building AI-BACKEND image..."
docker build \
    -f AI-BACKEND/Dockerfile \
    -t erp03/ai-backend:latest \
    --build-arg ENV=production \
    AI-BACKEND/

if [ $? -eq 0 ]; then
    echo "✅ AI-BACKEND image built successfully"
else
    echo "❌ Failed to build AI-BACKEND image"
    exit 1
fi

# Build frontend images (if Dockerfiles exist)
FRONTEND_APPS=("mrp" "ecommerce" "pos" "bi")

for app in "${FRONTEND_APPS[@]}"; do
    FRONTEND_DIR="frontend-$app"
    if [ -d "$FRONTEND_DIR" ] && [ -f "$FRONTEND_DIR/Dockerfile" ]; then
        echo "🏗️  Building frontend-$app image..."
        docker build \
            -f "$FRONTEND_DIR/Dockerfile" \
            -t "erp03/frontend-$app:latest" \
            "$FRONTEND_DIR/"
        
        if [ $? -eq 0 ]; then
            echo "✅ frontend-$app image built successfully"
        else
            echo "⚠️  Failed to build frontend-$app image (continuing...)"
        fi
    else
        echo "⚠️  Skipping frontend-$app (no Dockerfile)"
    fi
done

echo "✅ Image building completed"
echo ""
echo "Built images:"
docker images | grep "erp03/"
