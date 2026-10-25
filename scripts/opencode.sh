#!/usr/bin/env bash
set -euo pipefail
# Load user secrets if present
if [ -f "$HOME/.config/opencode/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$HOME/.config/opencode/.env"
  set +a
fi
exec /root/.opencode/bin/opencode "$@"
