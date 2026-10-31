#!/usr/bin/env bash
set -euo pipefail

# ERP03 Production Preflight Validation
# Usage: ./scripts/preflight.sh
# Validates all prerequisites before production deployment.

ERRORS=0
WARNINGS=0

check() {
    local label="$1"
    local result="$2"
    if [[ "$result" == "OK" ]]; then
        echo "  ✅ $label"
    elif [[ "$result" == "WARN" ]]; then
        echo "  ⚠️  $label"
        WARNINGS=$((WARNINGS + 1))
    else
        echo "  ❌ $label"
        ERRORS=$((ERRORS + 1))
    fi
}

echo "==> ERP03 Production Preflight Validation"
echo ""

# Required configuration
echo "── Configuration ──"
[[ -n "${SECRET_KEY:-}" ]] && [[ ${#SECRET_KEY} -ge 32 ]] && check "SECRET_KEY (>=32 chars)" "OK" || check "SECRET_KEY (>=32 chars)" "FAIL"
[[ -n "${DATABASE_URL:-}" ]] && check "DATABASE_URL set" "OK" || check "DATABASE_URL set" "FAIL"
[[ "$DATABASE_URL" == *"postgresql"* ]] && check "DATABASE_URL is PostgreSQL" "OK" || check "DATABASE_URL is PostgreSQL" "FAIL"
[[ -n "${CORS_ORIGINS:-}" ]] && check "CORS_ORIGINS set" "OK" || check "CORS_ORIGINS set" "FAIL"
[[ "$CORS_ORIGINS" != *"localhost"* ]] && check "CORS_ORIGINS no localhost" "OK" || check "CORS_ORIGINS no localhost" "FAIL"

# Required secrets
echo "── Secrets ──"
[[ -n "${GHCR_TOKEN:-}" ]] && check "GHCR_TOKEN set" "OK" || check "GHCR_TOKEN set" "WARN"
[[ -n "${DEPLOY_SSH_PRIVATE_KEY:-}" ]] && check "DEPLOY_SSH_PRIVATE_KEY set" "OK" || check "DEPLOY_SSH_PRIVATE_KEY set" "WARN"

# Kubernetes connectivity
echo "── Kubernetes ──"
if command -v kubectl &>/dev/null; then
    kubectl cluster-info --request-timeout=5s &>/dev/null && check "Kubernetes cluster reachable" "OK" || check "Kubernetes cluster reachable" "FAIL"
    kubectl get namespace erp03 &>/dev/null && check "Namespace 'erp03' exists" "OK" || check "Namespace 'erp03' exists" "WARN"
else
    check "kubectl available" "WARN"
fi

# Storage
echo "── Storage ──"
if command -v kubectl &>/dev/null; then
    kubectl get pvc -n erp03 &>/dev/null && check "PVCs exist" "OK" || check "PVCs exist" "WARN"
else
    check "PVC check (kubectl unavailable)" "WARN"
fi

# Database
echo "── Database ──"
if command -v pg_isready &>/dev/null; then
    pg_isready -h "${PGHOST:-localhost}" -p "${PGPORT:-5432}" &>/dev/null && check "PostgreSQL reachable" "OK" || check "PostgreSQL reachable" "FAIL"
else
    check "pg_isready available" "WARN"
fi

# Redis
echo "── Redis ──"
if command -v redis-cli &>/dev/null; then
    redis-cli -h "${REDIS_HOST:-localhost}" ping &>/dev/null && check "Redis reachable" "OK" || check "Redis reachable" "FAIL"
else
    check "redis-cli available" "WARN"
fi

# Docker
echo "── Docker ──"
if command -v docker &>/dev/null; then
    docker info &>/dev/null && check "Docker daemon running" "OK" || check "Docker daemon running" "WARN"
else
    check "Docker available" "WARN"
fi

# Manifest validation
echo "── Manifests ──"
MANIFEST_OK=true
for f in infra/kubernetes/base/*.yaml; do
    python3 -c "import yaml; yaml.safe_load(open('$f'))" 2>/dev/null || { MANIFEST_OK=false; break; }
done
$MANIFEST_OK && check "Kubernetes manifests valid YAML" "OK" || check "Kubernetes manifests valid YAML" "FAIL"

# Summary
echo ""
echo "==> Preflight Summary"
echo "    Errors: $ERRORS"
echo "    Warnings: $WARNINGS"
if [[ $ERRORS -gt 0 ]]; then
    echo "    STATUS: FAILED (fix errors before deploying)"
    exit 1
else
    echo "    STATUS: PASSED (warnings are non-blocking)"
    exit 0
fi
