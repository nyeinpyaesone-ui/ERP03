#!/bin/bash
# ERP SOLUTION — Docker Build & Push
# Run on your local machine

set -e

DOCKER_USER="powerrangeranikg"
VERSION="v1.0.0"

echo "ERP SOLUTION — Building Docker Images"
echo "====================================="
echo ""

# Login
echo "[1/5] Login to Docker Hub..."
docker login -u $DOCKER_USER
echo ""

# Build backend
echo "[2/5] Building backend..."
docker build -t $DOCKER_USER/erp-solution-backend:$VERSION ./backend
echo ""

# Build frontend
echo "[3/5] Building frontend..."
docker build -t $DOCKER_USER/erp-solution-frontend:$VERSION ./frontend
echo ""

# Tag latest
echo "[4/5] Tagging as latest..."
docker tag $DOCKER_USER/erp-solution-backend:$VERSION $DOCKER_USER/erp-solution-backend:latest
docker tag $DOCKER_USER/erp-solution-frontend:$VERSION $DOCKER_USER/erp-solution-frontend:latest
echo ""

# Push
echo "[5/5] Pushing to Docker Hub..."
docker push $DOCKER_USER/erp-solution-backend:$VERSION
docker push $DOCKER_USER/erp-solution-frontend:$VERSION
docker push $DOCKER_USER/erp-solution-backend:latest
docker push $DOCKER_USER/erp-solution-frontend:latest
echo ""

echo "====================================="
echo "✅ IMAGES LIVE ON DOCKER HUB!"
echo "====================================="
echo ""
echo "Verify:"
echo "  https://hub.docker.com/r/$DOCKER_USER/erp-solution-backend"
echo "  https://hub.docker.com/r/$DOCKER_USER/erp-solution-frontend"
echo ""
echo "Pull:"
echo "  docker pull $DOCKER_USER/erp-solution-backend:$VERSION"
echo "  docker pull $DOCKER_USER/erp-solution-frontend:$VERSION"
