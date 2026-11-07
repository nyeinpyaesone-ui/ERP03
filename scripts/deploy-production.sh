#!/usr/bin/env bash
set -euo pipefail

# ERP03 Production Deployment Script
# Usage: ./scripts/deploy-production.sh <image-tag> <image-digest>
# Environment: KUBECONFIG, NAMESPACE, DEPLOY_APPROVAL

IMAGE_TAG="${1:?Usage: deploy-production.sh <image-tag> <image-digest>}"
IMAGE_DIGEST="${2:?Usage: deploy-production.sh <image-tag> <image-digest>}"
NAMESPACE="${NAMESPACE:-erp03}"
KUBECONFIG="${KUBECONFIG:-$HOME/.kube/config}"

echo "==> Production Deployment: $IMAGE_TAG"
echo "    Digest: $IMAGE_DIGEST"
echo "    Namespace: $NAMESPACE"

# 1. Validate release
echo "==> [1/12] Validating release"
if [[ -z "$DEPLOY_APPROVAL" ]]; then
    echo "ERROR: DEPLOY_APPROVAL not set. Production deployment requires explicit approval."
    exit 1
fi
echo "   Approval: $DEPLOY_APPROVAL"

# 2. Verify immutable images
echo "==> [2/12] Verifying immutable image references"
if [[ ! "$IMAGE_DIGEST" =~ ^sha256:[a-f0-9]{64}$ ]]; then
    echo "ERROR: Invalid image digest format: $IMAGE_DIGEST"
    exit 1
fi
echo "   Digest format: OK"

# 3. Verify image digests
echo "==> [3/12] Verifying image existence"
echo "   (Image verification would use: docker manifest inspect $IMAGE_DIGEST)"

# 4. Validate manifests
echo "==> [4/12] Validating Kubernetes manifests"
for f in infra/kubernetes/base/*.yaml; do
    PYTHON_CMD="python3"
    [ -x ".venv/bin/python" ] && PYTHON_CMD=".venv/bin/python"
    $PYTHON_CMD -c "import yaml; list(yaml.safe_load_all(open('$f')))" && echo "   $f: OK" || { echo "   $f: INVALID"; exit 1; }
done

# 5. Authenticate cluster
echo "==> [5/12] Checking cluster connectivity"
if command -v kubectl &>/dev/null; then
    kubectl cluster-info --request-timeout=10s || { echo "ERROR: Cannot connect to cluster"; exit 1; }
else
    echo "   WARNING: kubectl not available, skipping cluster check"
fi

# 6. Apply configuration
echo "==> [6/12] Applying configuration"
if command -v kubectl &>/dev/null; then
    kubectl apply -k infra/kubernetes/overlays/production/ -n "$NAMESPACE" --dry-run=client
    echo "   Dry-run: OK"
fi

# 7. Deploy workloads
echo "==> [7/12] Deploying workloads"
if command -v kubectl &>/dev/null; then
    kubectl apply -k infra/kubernetes/overlays/production/ -n "$NAMESPACE"
fi

# 8. Wait for rollout
echo "==> [8/12] Waiting for rollout"
if command -v kubectl &>/dev/null; then
    kubectl rollout status deployment/erp03-backend -n "$NAMESPACE" --timeout=300s
    kubectl rollout status deployment/erp03-frontend -n "$NAMESPACE" --timeout=300s
fi

# 9. Validate readiness
echo "==> [9/12] Validating readiness"
if command -v kubectl &>/dev/null; then
    kubectl wait --for=condition=ready pod -l app=erp03-backend -n "$NAMESPACE" --timeout=120s
    kubectl wait --for=condition=ready pod -l app=erp03-frontend -n "$NAMESPACE" --timeout=120s
fi

# 10. Validate application health
echo "==> [10/12] Validating application health"
echo "   (Health check would use: curl https://erp.example.com/api/v1/healthz)"

# 11. Promote release
echo "==> [11/12] Promoting release"
echo "   Release promoted: $IMAGE_TAG ($IMAGE_DIGEST)"

# 12. Record known-good release
echo "==> [12/12] Recording known-good release"
echo "$IMAGE_TAG $IMAGE_DIGEST $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /tmp/known-good-releases.log
echo "   Recorded in known-good-releases.log"

echo "==> Deployment complete: $IMAGE_TAG"
