#!/usr/bin/env bash
set -euo pipefail

# ERP03 Security Audit Script
# Scans for secrets, vulnerabilities, and misconfigurations

echo "==> ERP03 Security Audit"
echo ""

ERRORS=0

# 1. Check for tracked .env files
echo "── Secret Tracking ──"
if git ls-files | grep -qE '\.env$|\.env\..*[^example]$'; then
    echo "  ❌ Tracked .env files found:"
    git ls-files | grep -E '\.env$|\.env\..*[^example]$'
    ERRORS=$((ERRORS + 1))
else
    echo "  ✅ No tracked .env files (only .example templates)"
fi

# 2. Check for hardcoded secrets in source
echo "── Hardcoded Secrets ──"
SECRET_PATTERNS="password\s*=\s*['\"][^'\"]{8,}['\"]|secret_key\s*=\s*['\"][^'\"]{8,}['\"]|api_key\s*=\s*['\"][^'\"]{8,}['\"]"
if grep -rnE "$SECRET_PATTERNS" --include="*.py" --include="*.yml" --include="*.yaml" --include="*.json" --include="*.sh" . 2>/dev/null | grep -v "example\|test\|spec\|.venv" | head -5; then
    echo "  ⚠️  Potential hardcoded secrets found (review above)"
    ERRORS=$((ERRORS + 1))
else
    echo "  ✅ No obvious hardcoded secrets"
fi

# 3. Check .gitignore covers sensitive files
echo "── .gitignore Coverage ──"
for pattern in ".env" "*.sqlite3" "node_modules" ".venv"; do
    if grep -q "$pattern" .gitignore; then
        echo "  ✅ $pattern in .gitignore"
    else
        echo "  ❌ $pattern NOT in .gitignore"
        ERRORS=$((ERRORS + 1))
    fi
done

# 4. Check Dockerfiles for non-root user
echo "── Container Security ──"
for df in ERP-BACKEND/Dockerfile frontend/Dockerfile; do
    if grep -q "USER " "$df"; then
        echo "  ✅ $df has USER directive"
    else
        echo "  ❌ $df missing USER directive (runs as root)"
        ERRORS=$((ERRORS + 1))
    fi
done

# 5. Check for mutable image tags in K8s
echo "── Image Immutability ──"
if grep -rn ":latest" infra/kubernetes/ 2>/dev/null | grep -v "sha256"; then
    echo "  ⚠️  Mutable :latest tags found in K8s manifests"
else
    echo "  ✅ No mutable :latest tags in K8s manifests"
fi

# 6. Check for secrets in K8s manifests
echo "── K8s Secret Hygiene ──"
if grep -rn "password.*=.*[a-zA-Z0-9]\{12,\}" infra/kubernetes/ 2>/dev/null | grep -v "REPLACE_WITH"; then
    echo "  ⚠️  Potential real secrets in K8s manifests"
else
    echo "  ✅ No real secrets in K8s manifests (placeholders only)"
fi

# 7. Python dependency audit
echo "── Dependency Audit ──"
if command -v pip-audit &>/dev/null; then
    cd ERP-BACKEND && pip-audit -r requirements.txt 2>&1 | tail -5
    cd ..
else
    echo "  ⚠️  pip-audit not available, skipping"
fi

echo ""
echo "==> Security Audit Complete"
echo "    Errors: $ERRORS"
if [[ $ERRORS -gt 0 ]]; then
    echo "    STATUS: ISSUES FOUND"
    exit 1
else
    echo "    STATUS: CLEAN"
    exit 0
fi
