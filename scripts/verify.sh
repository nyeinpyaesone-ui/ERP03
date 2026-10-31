# verify.sh — Repository Verification Entry Point

#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/ERP-BACKEND"

log() { printf '\033[1;32m==> %s\033[0m\n' "$*"; }

log "ERP03 Verification Gate"
log "========================"

cd "$ROOT_DIR"

# Run doctor.sh first
bash "$ROOT_DIR/scripts/doctor.sh"

# Run qualify.sh (full CI-equivalent gate)
log ""
log "Running full qualification gate"
bash "$ROOT_DIR/scripts/qualify.sh"

log ""
log "Verification gate complete. Repository is verified."
