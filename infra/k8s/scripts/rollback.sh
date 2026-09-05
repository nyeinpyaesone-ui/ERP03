#!/bin/bash
set -e

ENVIRONMENT=${1:-development}
NAMESPACE="erp03-${ENVIRONMENT}"

echo "=== ERP erp03 Kubernetes Rollback ==="
echo "Environment: ${ENVIRONMENT}"
echo ""

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo "Error: Environment must be development, staging, or production"
    exit 1
fi

# Production safety check
if [ "$ENVIRONMENT" == "production" ]; then
    read -p "Are you sure you want to ROLLBACK PRODUCTION? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Rollback cancelled"
        exit 0
    fi
fi

# Rollback deployments
echo "Rolling back deployments..."
kubectl rollout undo deployment/${ENVIRONMENT}-erp03-api -n ${NAMESPACE}
kubectl rollout undo deployment/${ENVIRONMENT}-erp03-web -n ${NAMESPACE}
kubectl rollout undo deployment/${ENVIRONMENT}-erp03-worker -n ${NAMESPACE}

# Wait for rollback
echo "Waiting for rollback to complete..."
kubectl rollout status deployment/${ENVIRONMENT}-erp03-api -n ${NAMESPACE} --timeout=300s
kubectl rollout status deployment/${ENVIRONMENT}-erp03-web -n ${NAMESPACE} --timeout=300s
kubectl rollout status deployment/${ENVIRONMENT}-erp03-worker -n ${NAMESPACE} --timeout=300s

echo ""
echo "Rollback completed successfully!"

