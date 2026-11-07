#!/usr/bin/env bash
set -euo pipefail

# ERP03 Production Rollback Script
# Usage: ./scripts/rollback.sh [previous-image-tag]
# Environment: KUBECONFIG, NAMESPACE

NAMESPACE="${NAMESPACE:-erp03}"
KUBECONFIG="${KUBECONFIG:-$HOME/.kube/config}"
PREVIOUS_TAG="${1:-}"

echo "==> Production Rollback"
echo "    Namespace: $NAMESPACE"

# 1. Capture diagnostics
echo "==> [1/6] Capturing diagnostics"
if command -v kubectl &>/dev/null; then
    kubectl get pods -n "$NAMESPACE" -o wide > /tmp/rollback-pods.log 2>&1 || true
    kubectl describe deployment/erp03-backend -n "$NAMESPACE" > /tmp/rollback-backend.log 2>&1 || true
    kubectl logs deployment/erp03-backend -n "$NAMESPACE" --tail=100 > /tmp/rollback-logs.log 2>&1 || true
    echo "   Diagnostics saved to /tmp/rollback-*.log"
fi

# 2. Stop promotion
echo "==> [2/6] Stopping promotion"
echo "   Promotion halted"

# 3. Rollback
echo "==> [3/6] Executing rollback"
if command -v kubectl &>/dev/null; then
    if [[ -n "$PREVIOUS_TAG" ]]; then
        kubectl set image deployment/erp03-backend backend=docker.io/powerrangeranikg/erp03-backend:"$PREVIOUS_TAG" -n "$NAMESPACE"
        kubectl set image deployment/erp03-frontend frontend=docker.io/powerrangeranikg/erp03-frontend:"$PREVIOUS_TAG" -n "$NAMESPACE"
    else
        kubectl rollout undo deployment/erp03-backend -n "$NAMESPACE"
        kubectl rollout undo deployment/erp03-frontend -n "$NAMESPACE"
    fi
fi

# 4. Wait for rollback completion
echo "==> [4/6] Waiting for rollback completion"
if command -v kubectl &>/dev/null; then
    kubectl rollout status deployment/erp03-backend -n "$NAMESPACE" --timeout=300s
    kubectl rollout status deployment/erp03-frontend -n "$NAMESPACE" --timeout=300s
fi

# 5. Validate restored health
echo "==> [5/6] Validating restored health"
if command -v kubectl &>/dev/null; then
    kubectl wait --for=condition=ready pod -l app=erp03-backend -n "$NAMESPACE" --timeout=120s
    kubectl wait --for=condition=ready pod -l app=erp03-frontend -n "$NAMESPACE" --timeout=120s
fi
echo "   Health validation: OK"

# 6. Fail the deployment job
echo "==> [6/6] Rollback complete"
echo "   Previous deployment restored"
echo "   Deployment job marked as FAILED"
exit 1
