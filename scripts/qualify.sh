#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/ERP-BACKEND"
FRONTEND_DIR="$ROOT_DIR/frontend"

: "${DATABASE_URL:=postgresql+asyncpg://erp03:erp03@127.0.0.1:5432/erp03}"

log() { printf '\n==> %s\n' "$*"; }

require_path() {
  local path="$1"
  local description="$2"
  [[ -e "$path" ]] || {
    printf 'qualification prerequisite missing: %s (%s)\n' "$path" "$description" >&2
    exit 1
  }
}

cd "$ROOT_DIR"

command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 2; }
command -v node >/dev/null || { echo "node is required" >&2; exit 2; }
command -v npm >/dev/null || { echo "npm is required" >&2; exit 2; }

log "Validate repository foundations"
require_path "$BACKEND_DIR/alembic.ini" "Alembic configuration"
require_path "$BACKEND_DIR/alembic/env.py" "Alembic environment"
require_path "$BACKEND_DIR/alembic/versions" "Alembic migration directory"
require_path "$BACKEND_DIR/app" "backend application package"
require_path "$FRONTEND_DIR/package.json" "frontend package manifest"

log "Backend syntax and production configuration"
cd "$BACKEND_DIR"
python3 -m compileall -q app alembic
ENVIRONMENT=production SECRET_KEY="qualification-secret-key-with-at-least-32-bytes" CORS_ORIGINS="https://erp.example.invalid" DATABASE_PATH="/tmp/erp03-qualification.sqlite3" python3 -c "from app.main import app; assert any(r.path == '/api/v1/auth/login' for r in app.routes); assert any(r.path == '/api/v1/sales' for r in app.routes); print('production configuration and critical routes: OK')"

log "Backend migration"
DATABASE_URL="$DATABASE_URL" alembic upgrade head

log "Backend tests"
DATABASE_URL="$DATABASE_URL" pytest -q

log "Frontend dependency/build"
cd "$FRONTEND_DIR"
npm install --no-audit --no-fund
npm run build

log "ERP03 qualification passed"
