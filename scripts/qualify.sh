#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/ERP-BACKEND"
FRONTEND_DIR="$ROOT_DIR/frontend"

log() { printf '\n==> %s\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

QUALIFY_LOG="${QUALIFY_LOG:-}"
QUALIFY_JSON=""
QUALIFY_STEPS=()
QUALIFY_CURRENT="init"
QUALIFY_USED_PG="false"

while [ $# -gt 0 ]; do
  case "$1" in
    --json-out)
      [ $# -ge 2 ] || die "--json-out requires a path"
      QUALIFY_JSON="$2"
      shift 2
      ;;
    *) die "unknown argument: $1" ;;
  esac
done

step_begin() { QUALIFY_CURRENT="$1"; log "$1"; }
step_done()  { QUALIFY_STEPS+=("$QUALIFY_CURRENT"); }

write_evidence() {
  local rc="$1" result="PASS" s
  [ "$rc" -ne 0 ] && result="FAIL"
  if [ -n "$QUALIFY_LOG" ]; then
    : > "$QUALIFY_LOG"
    for s in "${QUALIFY_STEPS[@]}"; do
      printf 'PASS\t%s\n' "$s" >> "$QUALIFY_LOG"
    done
    [ "$result" = "FAIL" ] && printf 'FAIL\t%s\n' "$QUALIFY_CURRENT" >> "$QUALIFY_LOG"
  fi
  [ -n "$QUALIFY_JSON" ] || return 0
  {
    printf '{"env":"%s","arch":"%s","commit":"%s","used_pg":%s,"steps":[' \
      "${AGENT_ENV_NAME:-local}" "$(uname -m)" \
      "$(git -C "$ROOT_DIR" rev-parse --short HEAD 2>/dev/null || echo none)" \
      "$QUALIFY_USED_PG"
    local first=1
    for s in "${QUALIFY_STEPS[@]}"; do
      [ "$first" -eq 1 ] && first=0 || printf ','
      printf '"%s"' "$s"
    done
    printf '],"current":"%s","result":"%s"}\n' "$QUALIFY_CURRENT" "$result"
  } > "$QUALIFY_JSON"
}

trap 'rc=$?; trap - EXIT; write_evidence "$rc"; exit "$rc"' EXIT

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
QUALIFY_USED_PG="false"
if probe_postgres "$DATABASE_URL"; then
  USE_PG=true
  QUALIFY_USED_PG="true"
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

step_begin "ruff"
cd "$BACKEND_DIR"
ruff check app tests alembic
ruff format --check app tests alembic
step_done

step_begin "compile"
python3 -m compileall -q app alembic
if $USE_PG; then
  ENVIRONMENT=production SECRET_KEY="qualification-secret-key-with-at-least-32-bytes" CORS_ORIGINS="https://erp.example.invalid" DATABASE_URL="$DATABASE_URL" DATABASE_PATH="/tmp/erp03-qualification.sqlite3" python3 -c "
from app.main import app
def _collect_paths(routes, out):
    for r in routes:
        p = getattr(r, 'path', None)
        if p:
            out.add(p)
        orig = getattr(r, 'original_router', None)
        if orig:
            _collect_paths(orig.routes, out)
paths = set()
_collect_paths(app.routes, paths)
assert any('/api/v1/auth/login' in p or p == '/auth/login' for p in paths), paths
assert any('/api/v1/sales' in p or p == '/sales' for p in paths), paths
print('production configuration and critical routes: OK')
"
else
  ENVIRONMENT=development SECRET_KEY="qualification-secret-key-with-at-least-32-bytes" CORS_ORIGINS="http://localhost:3000,http://localhost:5173" DATABASE_PATH="/tmp/erp03-qualification.sqlite3" python3 -c "
from app.main import app
def _collect_paths(routes, out):
    for r in routes:
        p = getattr(r, 'path', None)
        if p:
            out.add(p)
        orig = getattr(r, 'original_router', None)
        if orig:
            _collect_paths(orig.routes, out)
paths = set()
_collect_paths(app.routes, paths)
assert any('/api/v1/auth/login' in p or p == '/auth/login' for p in paths), paths
assert any('/api/v1/sales' in p or p == '/sales' for p in paths), paths
print('development configuration and critical routes: OK')
"
fi

step_begin "migrate"
DATABASE_URL="$DATABASE_URL" alembic upgrade head
step_done

step_begin "tests"
DATABASE_URL="$DATABASE_URL" pytest -q
step_done

step_begin "frontend"
cd "$FRONTEND_DIR"
npm ci --no-audit --no-fund
npm run build
step_done

log "ERP03 qualification passed"
