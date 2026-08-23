#!/bin/bash
set -e

ENVIRONMENT=${1:-development}
VERSION=${2:-latest}
NAMESPACE="erp_solution-${ENVIRONMENT}"

echo "=== ERP SOLUTION Kubernetes Deployment ==="
echo "Environment: ${ENVIRONMENT}"
echo "Version: ${VERSION}"
echo "Namespace: ${NAMESPACE}"
echo ""

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo "Error: Environment must be development, staging, or production"
    exit 1
fi

# Production safety check
if [ "$ENVIRONMENT" == "production" ]; then
    read -p "Are you sure you want to deploy to PRODUCTION? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Deployment cancelled"
        exit 0
    fi
fi

# Build and push images
echo "Building Docker images..."
docker build -t ghcr.io/nyeinpyaesone-ui/erp_solution-api:${VERSION} -f docker/Dockerfile.api ../
docker build -t ghcr.io/nyeinpyaesone-ui/erp_solution-web:${VERSION} -f docker/Dockerfile.web ../
docker build -t ghcr.io/nyeinpyaesone-ui/erp_solution-worker:${VERSION} -f docker/Dockerfile.worker ../

echo "Pushing Docker images..."
docker push ghcr.io/nyeinpyaesone-ui/erp_solution-api:${VERSION}
docker push ghcr.io/nyeinpyaesone-ui/erp_solution-web:${VERSION}
docker push ghcr.io/nyeinpyaesone-ui/erp_solution-worker:${VERSION}

# Update image tags in overlay
if [ "$VERSION" != "latest" ]; then
    sed -i "s/newTag: .*/newTag: ${VERSION}/g" overlays/${ENVIRONMENT}/kustomization.yaml
fi

# Apply Kubernetes manifests
echo "Applying Kubernetes manifests..."
kubectl apply -k overlays/${ENVIRONMENT}/

# Wait for rollout
echo "Waiting for deployment rollout..."
kubectl rollout status deployment/${ENVIRONMENT}-erp_solution-api -n ${NAMESPACE} --timeout=300s
kubectl rollout status deployment/${ENVIRONMENT}-erp_solution-web -n ${NAMESPACE} --timeout=300s
kubectl rollout status deployment/${ENVIRONMENT}-erp_solution-worker -n ${NAMESPACE} --timeout=300s

# Verify deployment
echo ""
echo "=== Deployment Status ==="
kubectl get pods -n ${NAMESPACE}
kubectl get svc -n ${NAMESPACE}
kubectl get ingress -n ${NAMESPACE}

echo ""
echo "Deployment to ${ENVIRONMENT} completed successfully!"

