#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/ERP-BACKEND"
FRONTEND_DIR="$ROOT_DIR/frontend"

: "${DATABASE_URL:=postgresql+asyncpg://erp03:erp03@127.0.0.1:5432/erp03}"

log() { printf '\n==> %s\n' "$*"; }

cd "$ROOT_DIR"

command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 2; }
command -v node >/dev/null || { echo "node is required" >&2; exit 2; }
command -v npm >/dev/null || { echo "npm is required" >&2; exit 2; }

log "Backend syntax"
cd "$BACKEND_DIR"
python3 -m compileall -q app alembic

log "Backend migration"
DATABASE_URL="$DATABASE_URL" alembic upgrade head

log "Backend tests"
DATABASE_URL="$DATABASE_URL" pytest -q

log "Frontend dependency/build"
cd "$FRONTEND_DIR"
npm install --no-audit --no-fund
npm run build

log "ERP03 qualification passed"
