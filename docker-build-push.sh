#!/bin/bash
###############################################################################
# ERP SOLUTION — Docker Build & Push Script
# Run this on your LOCAL MACHINE with Docker installed
###############################################################################

set -e

DOCKER_USERNAME="powerrangeranikg"
VERSION="${1:-v1.0.0}"

echo "=========================================="
echo "  ERP SOLUTION — Docker Build & Push"
echo "  Version: $VERSION"
echo "=========================================="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed"
    echo "Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if logged in
echo "[1/6] Checking Docker Hub login..."
if ! docker info 2>/dev/null | grep -q "Username"; then
    echo "  Please login first:"
    echo "  docker login -u $DOCKER_USERNAME"
    exit 1
fi
echo "  ✅ Logged in"

# Build backend
echo ""
echo "[2/6] Building backend image..."
docker build -t $DOCKER_USERNAME/erp-solution-backend:$VERSION ./backend
echo "  ✅ Backend built: $DOCKER_USERNAME/erp-solution-backend:$VERSION"

# Build frontend
echo ""
echo "[3/6] Building frontend image..."
docker build -t $DOCKER_USERNAME/erp-solution-frontend:$VERSION ./frontend
echo "  ✅ Frontend built: $DOCKER_USERNAME/erp-solution-frontend:$VERSION"

# Tag as latest
echo ""
echo "[4/6] Tagging as latest..."
docker tag $DOCKER_USERNAME/erp-solution-backend:$VERSION $DOCKER_USERNAME/erp-solution-backend:latest
docker tag $DOCKER_USERNAME/erp-solution-frontend:$VERSION $DOCKER_USERNAME/erp-solution-frontend:latest
echo "  ✅ Tagged as latest"

# Push versioned tags
echo ""
echo "[5/6] Pushing versioned images to Docker Hub..."
docker push $DOCKER_USERNAME/erp-solution-backend:$VERSION
docker push $DOCKER_USERNAME/erp-solution-frontend:$VERSION
echo "  ✅ Versioned images pushed"

# Push latest tags
echo ""
echo "[6/6] Pushing latest images..."
docker push $DOCKER_USERNAME/erp-solution-backend:latest
docker push $DOCKER_USERNAME/erp-solution-frontend:latest
echo "  ✅ Latest images pushed"

echo ""
echo "=========================================="
echo "  ✅ ALL IMAGES LIVE ON DOCKER HUB!"
echo "=========================================="
echo ""
echo "  Verify at:"
echo "  https://hub.docker.com/r/$DOCKER_USERNAME/erp-solution-backend"
echo "  https://hub.docker.com/r/$DOCKER_USERNAME/erp-solution-frontend"
echo ""
echo "  Pull commands:"
echo "  docker pull $DOCKER_USERNAME/erp-solution-backend:$VERSION"
echo "  docker pull $DOCKER_USERNAME/erp-solution-frontend:$VERSION"
echo ""
