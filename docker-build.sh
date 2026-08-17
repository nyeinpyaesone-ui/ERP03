#!/bin/bash
# ERP03 — Docker Build & Push
# Credentials must be supplied by Docker's credential helper or interactive login.
set -euo pipefail

DOCKER_USER="${DOCKER_USER:-powerrangeranikg}"
VERSION="${VERSION:-v1.0.0}"

printf '%s\n' "ERP03 — Building Docker Images"

# ERP system-of-record backend
docker build -t "$DOCKER_USER/erp-solution-backend:$VERSION" ./ERP-BACKEND

# ERP web application
docker build -t "$DOCKER_USER/erp-solution-frontend:$VERSION" ./ERP-BACKEND/frontend-react

docker tag "$DOCKER_USER/erp-solution-backend:$VERSION" "$DOCKER_USER/erp-solution-backend:latest"
docker tag "$DOCKER_USER/erp-solution-frontend:$VERSION" "$DOCKER_USER/erp-solution-frontend:latest"

docker push "$DOCKER_USER/erp-solution-backend:$VERSION"
docker push "$DOCKER_USER/erp-solution-frontend:$VERSION"
docker push "$DOCKER_USER/erp-solution-backend:latest"
docker push "$DOCKER_USER/erp-solution-frontend:latest"

printf '%s\n' "Docker images published successfully."
