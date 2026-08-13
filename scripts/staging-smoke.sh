#!/usr/bin/env bash
###############################################################################
# ERP03 — Staging Smoke Test
# Usage: API_BASE_URL=https://staging-api.example.com ./scripts/staging-smoke.sh
###############################################################################
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-}"
if [ -z "$API_BASE_URL" ]; then
  echo "ERROR: API_BASE_URL is required"
  exit 2
fi

API_BASE_URL="${API_BASE_URL%/}"

check() {
  local name="$1"
  local url="$2"
  local expected="${3:-200}"
  local code
  code="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 10 --max-time 30 "$url")"
  if [ "$code" != "$expected" ]; then
    echo "FAIL: $name ($url) returned HTTP $code; expected $expected"
    exit 1
  fi
  echo "PASS: $name"
}

check "API health" "$API_BASE_URL/health"
check "Prometheus metrics" "$API_BASE_URL/metrics"

echo "PASS: staging smoke test completed"
