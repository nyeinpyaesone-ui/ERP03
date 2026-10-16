#!/usr/bin/env bash
# Post-deployment smoke test against a running ERP03 stack.
#
# Usage:
#   BASE_URL=http://localhost:8000 FRONTEND_URL=http://localhost:3000 ./scripts/smoke.sh
#
# Verifies the invariants every environment must satisfy before traffic is
# declared healthy: liveness, readiness (database reachable and migrated),
# metrics exposition, and the frontend entry point.
set -Eeuo pipefail

: "${BASE_URL:=http://localhost:8000}"
: "${FRONTEND_URL:=http://localhost:3000}"
: "${TIMEOUT:=10}"

failures=0
check() {
  local name="$1" url="$2"
  if body="$(curl -fsS --max-time "$TIMEOUT" "$url" 2>&1)"; then
    printf '[smoke] PASS %s\n' "$name"
    printf '[smoke]      %s\n' "$(printf '%s' "$body" | head -c 200)"
  else
    printf '[smoke] FAIL %s (%s)\n' "$name" "$body" >&2
    failures=$((failures + 1))
  fi
}

command -v curl >/dev/null || { echo "curl is required" >&2; exit 2; }

log_root() { check "api identity" "${BASE_URL}/api/v1"; }
health() { check "liveness /healthz" "${BASE_URL}/api/v1/healthz"; }
ready() { check "readiness /readyz" "${BASE_URL}/api/v1/readyz"; }
metrics() {
  if curl -fsS --max-time "$TIMEOUT" "${BASE_URL}/metrics" | grep -q erp03_http_requests_total; then
    printf '[smoke] PASS metrics exposition\n'
  else
    printf '[smoke] FAIL metrics exposition\n' >&2
    failures=$((failures + 1))
  fi
}
frontend() { check "frontend entry" "${FRONTEND_URL}/"; }

log_root
health
ready
metrics
frontend

if [[ "$failures" -gt 0 ]]; then
  printf '\n[smoke] %d check(s) failed\n' "$failures" >&2
  exit 1
fi
printf '\n[smoke] all checks passed\n'
