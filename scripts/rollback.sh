#!/usr/bin/env bash
set -Eeuo pipefail

# Roll back exactly one ERP03 Kubernetes Deployment.
# Usage:
#   ./scripts/rollback.sh backend
#   ./scripts/rollback.sh frontend --revision 12
#   ./scripts/rollback.sh backend --image ghcr.io/nyeinpyaesone-ui/erp03-backend@sha256:<64-hex>
# Environment: KUBECONFIG, NAMESPACE

NAMESPACE="\${NAMESPACE:-erp03}"
export KUBECONFIG="\${KUBECONFIG:-$HOME/.kube/config}"
DEPLOYMENT="\${1:-}"
MODE="\${2:-}"
VALUE="\${3:-}"

case "$DEPLOYMENT" in
  backend|frontend) ;;
  *)
    echo "ERROR: choose exactly one Deployment: backend or frontend" >&2
    exit 2
    ;;
esac

RESOURCE="deployment/erp03-$DEPLOYMENT"
CONTAINER="$DEPLOYMENT"
EXPECTED_IMAGE="ghcr.io/nyeinpyaesone-ui/erp03-$DEPLOYMENT"

if [[ $# -gt 3 ]]; then
  echo "ERROR: too many arguments" >&2
  exit 2
fi

case "$MODE" in
  "")
    if [[ $# -gt 1 ]]; then
      echo "ERROR: provide --revision N or --image IMAGE@sha256:DIGEST" >&2
      exit 2
    fi
    ;;
  --revision)
    [[ "$VALUE" =~ ^[1-9][0-9]*$ ]] || {
      echo "ERROR: revision must be a positive integer" >&2
      exit 2
    }
    ;;
  --image)
    [[ "$VALUE" == "$EXPECTED_IMAGE@sha256:"* ]] || {
      echo "ERROR: image must use the matching GHCR repository: $EXPECTED_IMAGE" >&2
      exit 2
    }
    DIGEST="\${VALUE##*@sha256:}"
    [[ "$DIGEST" =~ ^[a-f0-9]{64}$ ]] || {
      echo "ERROR: image must be pinned by a 64-character sha256 digest" >&2
      exit 2
    }
    ;;
  *)
    echo "ERROR: supported modes are --revision and --image" >&2
    exit 2
    ;;
esac

command -v kubectl >/dev/null 2>&1 || {
  echo "ERROR: kubectl is required" >&2
  exit 2
}
kubectl cluster-info --request-timeout=10s >/dev/null
kubectl get "$RESOURCE" -n "$NAMESPACE" >/dev/null

echo "==> ERP03 application rollback"
echo "    Namespace: $NAMESPACE"
echo "    Target:    $RESOURCE"
echo "==> Current rollout history"
kubectl rollout history "$RESOURCE" -n "$NAMESPACE"

if [[ "$MODE" == "--image" ]]; then
  echo "==> Restoring the explicitly supplied immutable image digest"
  kubectl set image "$RESOURCE" "$CONTAINER=$VALUE" -n "$NAMESPACE"
elif [[ "$MODE" == "--revision" ]]; then
  echo "==> Restoring recorded Deployment revision $VALUE"
  kubectl rollout undo "$RESOURCE" --to-revision="$VALUE" -n "$NAMESPACE"
else
  echo "==> Restoring the immediately previous Deployment revision"
  kubectl rollout undo "$RESOURCE" -n "$NAMESPACE"
fi

echo "==> Waiting for only $RESOURCE to become available"
kubectl rollout status "$RESOURCE" -n "$NAMESPACE" --timeout=300s

echo "==> Rollback completed for $RESOURCE"
echo "    Other application Deployments were not changed."
