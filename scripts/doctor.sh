# doctor.sh — Repository Health Check

#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/ERP-BACKEND"
FRONTEND_DIR="$ROOT_DIR/frontend"

log() { printf '\033[1;32m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }
fail() { printf '\033[1;31mFAIL:\033[0m %s\n' "$*" >&2; exit 1; }

log "ERP03 Repository Health Check"
log "=============================="

# 1. Git state
log "1. Git state"
git -C "$ROOT_DIR" status --short | grep -q . && fail "Working tree is not clean" || echo "  OK: working tree clean"
git -C "$ROOT_DIR" rev-parse --abbrev-ref HEAD

# 2. Backend lint/format/compile
log "2. Backend quality gates"
cd "$BACKEND_DIR"
if [ -x .venv/bin/ruff ]; then
  .venv/bin/ruff check app tests alembic || fail "ruff check failed"
  .venv/bin/ruff format --check app tests alembic || fail "ruff format check failed"
  echo "  OK: ruff check + format"
else
  warn "ruff not found in .venv; run ./scripts/setup.sh first"
fi
python3 -m compileall -q app alembic && echo "  OK: compileall"

# 3. Backend tests
log "3. Backend tests"
cd "$BACKEND_DIR"
if [ -x .venv/bin/python ]; then
  .venv/bin/python -m pytest -q || fail "pytest failed"
  echo "  OK: pytest"
else
  warn "python venv not found; run ./scripts/setup.sh first"
fi

# 4. Frontend build
log "4. Frontend build"
cd "$FRONTEND_DIR"
if [ -f package-lock.json ] && command -v npm >/dev/null 2>&1; then
  npm ci --no-audit --no-fund --silent || fail "npm ci failed"
  npm run build || fail "npm run build failed"
  echo "  OK: frontend build"
else
  warn "package-lock.json or npm missing; frontend build skipped"
fi

# 5. Compose config validation
log "5. Docker Compose configuration"
cd "$ROOT_DIR"
if command -v docker compose >/dev/null 2>&1; then
  POSTGRES_PASSWORD=testpass CORS_ORIGINS=https://erp.example.com SECRET_KEY=0123456789abcdef0123456789abcdef DATABASE_URL=postgresql+asyncpg://erp03:testpass@postgres:5432/erp03 docker compose -f docker-compose.yml config --quiet || fail "prod compose config invalid"
  docker compose -f docker-compose.dev.yml config --quiet || fail "dev compose config invalid"
  echo "  OK: both compose files valid"
else
  warn "docker compose not found; compose validation skipped"
fi

# 6. Alembic migration head
log "6. Alembic migration head"
cd "$BACKEND_DIR"
if [ -x .venv/bin/alembic ]; then
  HEADS=$(.venv/bin/alembic heads 2>/dev/null | grep -c "head") || true
  if [ "$HEADS" -eq 1 ]; then
    echo "  OK: single alembic head"
  else
    fail "multiple alembic heads detected"
  fi
else
  warn "alembic not found in .venv"
fi

log ""
log "Repository health check complete."
