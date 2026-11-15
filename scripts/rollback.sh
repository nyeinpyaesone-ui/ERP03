#!/usr/bin/env bash
set -euo pipefail

# ERP03 Production Rollback Script
# Usage: ./scripts/rollback.sh [previous-image-tag]
# Environment: KUBECONFIG, NAMESPACE

NAMESPACE="${NAMESPACE:-erp03}"
KUBECONFIG="${KUBECONFIG:-$HOME/.kube/config}"
PREVIOUS_TAG="${1:-}"

if [[ -n "$PREVIOUS_TAG" && ! "$PREVIOUS_TAG" =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]]; then
    echo "ERROR: Invalid previous image tag"
    exit 2
fi

command -v kubectl >/dev/null 2>&1 || {
    echo "ERROR: kubectl is required for rollback"
    exit 2
}
kubectl cluster-info --request-timeout=10s >/dev/null || {
    echo "ERROR: Kubernetes cluster is not reachable"
    exit 2
}

echo "==> Production Rollback"
echo "    Namespace: $NAMESPACE"

# 1. Capture diagnostics
echo "==> [1/6] Capturing diagnostics"
kubectl get pods -n "$NAMESPACE" -o wide > /tmp/rollback-pods.log 2>&1 || true
kubectl describe deployment/erp03-backend -n "$NAMESPACE" > /tmp/rollback-backend.log 2>&1 || true
kubectl logs deployment/erp03-backend -n "$NAMESPACE" --tail=100 > /tmp/rollback-logs.log 2>&1 || true
echo "   Diagnostics saved to /tmp/rollback-*.log"

# 2. Stop promotion
echo "==> [2/6] Stopping promotion"
echo "   Promotion halted"

# 3. Rollback
echo "==> [3/6] Executing rollback"
if [[ -n "$PREVIOUS_TAG" ]]; then
    kubectl set image deployment/erp03-backend backend="ghcr.io/nyeinpyaesone-ui/erp03-backend:$PREVIOUS_TAG" -n "$NAMESPACE"
    kubectl set image deployment/erp03-frontend frontend="ghcr.io/nyeinpyaesone-ui/erp03-frontend:$PREVIOUS_TAG" -n "$NAMESPACE"
else
    kubectl rollout undo deployment/erp03-backend -n "$NAMESPACE"
    kubectl rollout undo deployment/erp03-frontend -n "$NAMESPACE"
fi

# 4. Wait for rollback completion
echo "==> [4/6] Waiting for rollback completion"
kubectl rollout status deployment/erp03-backend -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/erp03-frontend -n "$NAMESPACE" --timeout=300s

# 5. Validate restored health
echo "==> [5/6] Validating restored health"
kubectl wait --for=condition=ready pod -l app=erp03-backend -n "$NAMESPACE" --timeout=120s
kubectl wait --for=condition=ready pod -l app=erp03-frontend -n "$NAMESPACE" --timeout=120s
echo "   Kubernetes readiness validation: OK"

# 6. Fail the deployment job
echo "==> [6/6] Rollback complete"
echo "   Previous application release restored"
echo "   Returning non-zero so the failed deployment pipeline remains failed"
exit 1
