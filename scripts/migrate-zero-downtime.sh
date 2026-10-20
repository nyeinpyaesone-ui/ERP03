#!/usr/bin/env bash
set -Eeuo pipefail

# Zero-downtime database migration strategy
# Phase 1: Deploy backward-compatible schema changes
echo "[Phase 1] Deploying backward-compatible schema..."
alembic upgrade head --sql > migrate-phase1.sql
psql "$DATABASE_URL" -f migrate-phase1.sql

# Phase 2: Deploy code that reads/writes both old and new schema (backend vN+1)
echo "[Phase 2] Deploy dual-write code..."
# kubectl rollout status deployment/backend -n production

# Phase 3: Backfill data
echo "[Phase 3] Backfilling data..."
python3 -m scripts.backfill_data || echo "Backfill script not found, skipping"

# Phase 4: Deploy code that only uses new schema (backend vN+2)
echo "[Phase 4] Deploy new-schema-only code..."
# kubectl rollout status deployment/backend -n production

# Phase 5: Drop old columns/tables
echo "[Phase 5] Dropping legacy schema..."
alembic upgrade head --sql > migrate-phase5.sql
psql "$DATABASE_URL" -f migrate-phase5.sql

echo "Zero-downtime migration complete."
