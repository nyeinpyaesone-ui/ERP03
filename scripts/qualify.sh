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
ALLOW_SQLITE_SMOKE=false
QUALIFY_MODE="full"
QUALIFY_DATABASE="unknown"

while [ $# -gt 0 ]; do
  case "$1" in
    --json-out)
      [ $# -ge 2 ] || die "--json-out requires a path"
      QUALIFY_JSON="$2"
      shift 2
      ;;
    --allow-sqlite-smoke) ALLOW_SQLITE_SMOKE=true ;;
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
    printf '{"env":"%s","arch":"%s","commit":"%s","used_pg":%s,"database":"%s","qualification":"%s","steps":[' \
      "${AGENT_ENV_NAME:-local}" "$(uname -m)" \
      "$(git -C "$ROOT_DIR" rev-parse --short HEAD 2>/dev/null || echo none)" \
      "$QUALIFY_USED_PG" "$QUALIFY_DATABASE" "$QUALIFY_MODE"
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

python -c 'import sys; assert sys.version_info[:2] == (3, 12), f"Python 3.12 required, found {sys.version.split()[0]}"' || die "Qualification requires the Python 3.12 virtualenv used by CI."
command -v node >/dev/null || { echo "node is required" >&2; exit 2; }
command -v npm >/dev/null || { echo "npm is required" >&2; exit 2; }
node -e 'const [major, minor] = process.versions.node.split(".").map(Number); process.exit(major === 22 && minor >= 12 ? 0 : 1)' || die "Qualification requires Node.js 22.12+ to match CI."

# ---------------------------------------------------------------------------
# Database qualification is strict by default. SQLite is an explicit smoke
# mode only and must never be reported as PostgreSQL/full qualification.
# ---------------------------------------------------------------------------
DEFAULT_PG_URL="postgresql+asyncpg://erp03:erp03@127.0.0.1:5432/erp03"
SQLITE_URL="sqlite+aiosqlite:////tmp/erp03-qualify.sqlite3"
: "${DATABASE_URL:=$DEFAULT_PG_URL}"

probe_postgres() {
  local url="$1"
  [[ "$url" == postgresql+asyncpg://* ]] || return 1
  DATABASE_URL_TO_PROBE="$url" python - <<'PY' >/dev/null 2>&1
import asyncio
import os
import asyncpg

async def main():
    try:
        # SQLAlchemy's asyncpg dialect URL is not accepted by asyncpg.connect().
        # Normalize only the driver marker while preserving credentials/options.
        database_url = os.environ["DATABASE_URL_TO_PROBE"].replace(
            "postgresql+asyncpg://", "postgresql://", 1
        )
        conn = await asyncpg.connect(database_url, timeout=3)
        await conn.close()
    except Exception:
        raise SystemExit(1)

asyncio.run(main())
PY
}

USE_PG=false
QUALIFY_USED_PG="false"
if probe_postgres "$DATABASE_URL"; then
  USE_PG=true
  QUALIFY_USED_PG="true"
  QUALIFY_DATABASE="postgresql"
  QUALIFY_MODE="full"
  log "PostgreSQL is reachable; running full database qualification."
else
  if ! $ALLOW_SQLITE_SMOKE; then
    die "PostgreSQL is unavailable. Full qualification requires PostgreSQL; start the dev database or set DATABASE_URL. Use --allow-sqlite-smoke only for a clearly labelled, non-production smoke run."
  fi
  warn "Running SQLite smoke-only mode. PostgreSQL migrations and row-lock concurrency are NOT qualified."
  DATABASE_URL="$SQLITE_URL"
  export DATABASE_URL
  ENVIRONMENT=development
  export ENVIRONMENT
  QUALIFY_DATABASE="sqlite"
  QUALIFY_MODE="smoke-only"
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
python -m compileall -q app alembic
if $USE_PG; then
  ENVIRONMENT=production SECRET_KEY="qualification-secret-key-with-at-least-32-bytes" CORS_ORIGINS="https://erp.example.invalid" DATABASE_URL="$DATABASE_URL" DATABASE_PATH="/tmp/erp03-qualification.sqlite3" python -c "
from app.main import app
def _collect_paths(routes, out):
    for r in routes:
        p = getattr(r, 'path', None)
        if p:
            out.add(p)
        # FastAPI 0.162+: included routers expose routes via original_router
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
  ENVIRONMENT=development SECRET_KEY="qualification-secret-key-with-at-least-32-bytes" CORS_ORIGINS="http://localhost:3000,http://localhost:5173" DATABASE_PATH="/tmp/erp03-qualification.sqlite3" python -c "
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

if [[ "$QUALIFY_MODE" == "smoke-only" ]]; then
  log "ERP03 SQLite smoke checks passed; PostgreSQL/full qualification remains pending"
else
  log "ERP03 PostgreSQL qualification passed"
fi
