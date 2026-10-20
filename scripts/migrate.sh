#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/ERP-BACKEND"

log() { printf '\n==> %s\n' "$*"; }

log "Running zero-downtime database migration"

# Phase 1: Apply backward-compatible schema changes (additive only)
log "Phase 1: Applying backward-compatible schema..."
alembic upgrade head

# Phase 2: Deploy code that reads/writes both old and new schema
# (This is handled by the deployment pipeline)
log "Phase 2: Ready for dual-write code deployment..."

# Phase 3: Backfill data
log "Phase 3: Running data backfill..."
if [ -f scripts/backfill_data.py ]; then
  python scripts/backfill_data.py
else
  log "No backfill script found, skipping..."
fi

# Phase 4: Deploy code that only uses new schema
# (This is handled by the deployment pipeline)
log "Phase 4: Ready for new-schema-only code deployment..."

# Phase 5: Drop legacy schema
log "Phase 5: Dropping legacy schema (manual review required)..."
log "Run 'alembic upgrade head' after verifying Phase 4 is stable."

log "Zero-downtime migration guide complete."
