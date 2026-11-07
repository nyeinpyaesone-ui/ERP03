#!/usr/bin/env bash
set -Eeuo pipefail

AGENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env.sh
source "$AGENT_DIR/env.sh"
agent_detect
cd "$AGENT_ROOT_DIR"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT=".agent/evidence"
mkdir -p "$OUT"
agent_record_env "$OUT"

JSON="$PWD/$OUT/$STAMP.json"
LOG="$PWD/$OUT/$STAMP.steps.log"

set +e
QUALIFY_LOG="$LOG" bash scripts/qualify.sh --json-out "$JSON"
RC=$?
set -e

if [ ! -s "$JSON" ]; then
  printf '{"env":"%s","arch":"%s","used_pg":false,"steps":[],"result":"FAIL"}\n' \
    "$AGENT_ENV_NAME" "$AGENT_ARCH" > "$JSON"
fi

echo
if [ "$AGENT_DOCKER" -eq 1 ]; then
  echo "[PASS] docker        daemon reachable"
else
  printf '[SKIP] docker        reason=no-daemon (%s)\n' "$AGENT_ENV_NAME"
fi

if grep -q '"used_pg": *false' "$JSON"; then
  echo "[SKIP] postgres      reason=sqlite-fallback"
else
  echo "[PASS] postgres      reachable"
fi

if [ -x .venv/bin/mypy ] || command -v mypy >/dev/null 2>&1; then
  echo "[INFO] mypy          installed (advisory, not gating)"
else
  echo "[SKIP] mypy          reason=not-installed"
fi

echo "EVIDENCE $JSON"
if [ "$RC" -eq 0 ]; then
  echo "RESULT PASS"
else
  echo "RESULT FAIL"
fi
exit "$RC"
