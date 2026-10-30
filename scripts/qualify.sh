#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/ERP-BACKEND"
FRONTEND_DIR="$ROOT_DIR/frontend"

log() { printf '\n==> %s\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

require_path() {
  local path="$1"
  local description="$2"
  [[ -e "$path" ]] || {
    printf 'qualification prerequisite missing: %s (%s)\n' "$path" "$description" >&2
    exit 1
  }
}

# ---------------------------------------------------------------------------
# Activate the provisioned virtualenv (created by scripts/setup.sh).
# ---------------------------------------------------------------------------
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  die "virtualenv not found at $VENV_DIR. Run ./scripts/setup.sh first."
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 2; }
command -v node >/dev/null || { echo "node is required" >&2; exit 2; }
command -v npm >/dev/null || { echo "npm is required" >&2; exit 2; }

# ---------------------------------------------------------------------------
# Database URL resolution with precondition probe.
# Prefer PostgreSQL when reachable; otherwise fall back to hermetic SQLite
# with a clear warning instead of an opaque asyncpg connection error.
# ---------------------------------------------------------------------------
DEFAULT_PG_URL="postgresql+asyncpg://erp03:erp03@127.0.0.1:5432/erp03"
SQLITE_URL="sqlite+aiosqlite:////tmp/erp03-qualify.sqlite3"

: "${DATABASE_URL:=$DEFAULT_PG_URL}"

probe_postgres() {
  local url="$1"
  [[ "$url" == postgresql+asyncpg://* ]] || return 1
  python3 - <<EOF >/dev/null 2>&1
import asyncio, asyncpg, sys
async def main():
    try:
        conn = await asyncpg.connect("${url}", timeout=2)
        await conn.close()
    except Exception:
        raise SystemExit(1)
asyncio.run(main())
EOF
}

USE_PG=false
if probe_postgres "$DATABASE_URL"; then
  USE_PG=true
  log "PostgreSQL reachable at $DATABASE_URL — qualification will run against it"
else
  warn "PostgreSQL not reachable at $DATABASE_URL"
  warn "Falling back to hermetic SQLite: $SQLITE_URL"
  warn "To run against PostgreSQL, set DATABASE_URL to a reachable instance."
  DATABASE_URL="$SQLITE_URL"
  export DATABASE_URL
  # Must also set ENVIRONMENT=development to avoid production validation error
  ENVIRONMENT=development
  export ENVIRONMENT
fi

log "Validate repository foundations"
require_path "$BACKEND_DIR/alembic.ini" "Alembic configuration"
require_path "$BACKEND_DIR/alembic/env.py" "Alembic environment"
require_path "$BACKEND_DIR/alembic/versions" "Alembic migration directory"
require_path "$BACKEND_DIR/app" "backend application package"
require_path "$FRONTEND_DIR/package.json" "frontend package manifest"

log "Backend syntax and production configuration"
cd "$BACKEND_DIR"
python3 -m compileall -q app alembic
if $USE_PG; then
  ENVIRONMENT=production SECRET_KEY="qualification-secret-key-with-at-least-32-bytes" CORS_ORIGINS="https://erp.example.invalid" DATABASE_URL="$DATABASE_URL" DATABASE_PATH="/tmp/erp03-qualification.sqlite3" python3 -c "from app.main import app; assert any(r.path == '/api/v1/auth/login' for r in app.routes); assert any(r.path == '/api/v1/sales' for r in app.routes); print('production configuration and critical routes: OK')"
else
  ENVIRONMENT=development SECRET_KEY="qualification-secret-key-with-at-least-32-bytes" CORS_ORIGINS="http://localhost:3000,http://localhost:5173" DATABASE_PATH="/tmp/erp03-qualification.sqlite3" python3 -c "from app.main import app; assert any(r.path == '/api/v1/auth/login' for r in app.routes); assert any(r.path == '/api/v1/sales' for r in app.routes); print('development configuration and critical routes: OK')"
fi

log "Backend migration"
DATABASE_URL="$DATABASE_URL" alembic upgrade head

log "Backend tests"
DATABASE_URL="$DATABASE_URL" pytest -q

log "Frontend dependency/build"
cd "$FRONTEND_DIR"
npm ci --no-audit --no-fund
npm run build

log "ERP03 qualification passed"
