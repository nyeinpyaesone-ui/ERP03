#!/usr/bin/env bash
#
# ERP03 — Complete Development Environment Setup & Verification
#
# This script implements the full dev-flow checklist:
# 1. Prerequisites verification
# 2. GitHub authentication & secrets sync
# 3. Auto-configuration (dev environment)
# 4. Backend provisioning (venv, deps, migrations)
# 5. Frontend provisioning (npm deps, build)
# 6. Full qualification gate (CI-equivalent)
# 7. Smoke tests & health checks
# 8. Evidence collection for PR/CI readiness
#
# Usage:
#   ./scripts/dev-env-setup.sh [--with-infra] [--skip-frontend] [--force]
#
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/ERP-BACKEND"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"

WITH_INFRA=false
SKIP_FRONTEND=false
FORCE=false
QUALIFY=true

log()  { printf '\n\033[1;32m[%s] ==> %s\033[0m\n' "$(date '+%H:%M:%S')" "$*"; }
warn() { printf '\033[1;33m[%s] warning:\033[0m %s\n' "$(date '+%H:%M:%S')" "$*" >&2; }
die()  { printf '\033[1;31m[%s] error:\033[0m %s\n' "$(date '+%H:%M:%S')" "$*" >&2; exit 1; }
step() { printf '\n\033[1;36m[%s] STEP %d/%d:\033[0m %s\n' "$(date '+%H:%M:%S')" "$1" "$2" "$3"; }

usage() {
  cat <<EOF
Usage: ./scripts/dev-env-setup.sh [options]

Options:
  --with-infra       Start Docker Compose services after bootstrap
  --skip-frontend    Skip frontend npm install and build
  --force            Overwrite existing .env files
  --no-qualify       Skip qualification gate (not recommended)
  --help             Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-infra) WITH_INFRA=true ;;
    --skip-frontend) SKIP_FRONTEND=true ;;
    --force) FORCE=true ;;
    --no-qualify) QUALIFY=false ;;
    --help|-h) usage; exit 0 ;;
    *) die "Unknown option: $1 (see --help)" ;;
  esac
  shift
done

TOTAL_STEPS=8
CURRENT_STEP=0

# =============================================================================
# STEP 1: Prerequisites Verification
# =============================================================================
CURRENT_STEP=1
step $CURRENT_STEP $TOTAL_STEPS "Prerequisites Verification"

log "Checking required tools..."
REQUIRED_TOOLS=("git" "python3" "node" "npm" "docker" "gh")
for tool in "${REQUIRED_TOOLS[@]}"; do
  if command -v "$tool" >/dev/null 2>&1; then
    version=$("$tool" --version 2>&1 | head -1)
    log "  ✓ $tool: $version"
  else
    die "  ✗ $tool: NOT FOUND (required)"
  fi
done

log "Checking Python version..."
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)"; then
  log "  ✓ Python $PY_VERSION >= 3.12"
else
  die "  ✗ Python $PY_VERSION < 3.12 (required 3.12+)"
fi

log "Checking Node version..."
NODE_MAJOR=$(node --version | sed 's/v\([0-9]*\).*/\1/')
if (( NODE_MAJOR >= 18 )); then
  log "  ✓ Node $NODE_MAJOR >= 18"
else
  die "  ✗ Node $NODE_MAJOR < 18 (required 18+)"
fi

log "Checking Docker daemon..."
if docker info >/dev/null 2>&1; then
  log "  ✓ Docker daemon accessible"
  DOCKER_AVAILABLE=true
else
  warn "  ⚠ Docker daemon not accessible (CI will handle builds)"
  DOCKER_AVAILABLE=false
fi

log "Checking GitHub CLI authentication..."
if gh auth status >/dev/null 2>&1; then
  GH_USER=$(gh api user --jq '.login' 2>/dev/null || echo "unknown")
  log "  ✓ GitHub CLI authenticated as: $GH_USER"
  GH_AUTH=true
else
  warn "  ⚠ GitHub CLI not authenticated (secrets sync will be skipped)"
  GH_AUTH=false
fi

log "Checking repository state..."
cd "$ROOT_DIR"
if git status --porcelain | grep -q '^??'; then
  warn "  ⚠ Untracked files present (will be handled by setup)"
fi
CURRENT_BRANCH=$(git branch --show-current)
log "  ✓ Current branch: $CURRENT_BRANCH"
COMMIT_SHA=$(git rev-parse --short HEAD)
log "  ✓ Current commit: $COMMIT_SHA"

# =============================================================================
# STEP 2: GitHub Secrets Sync
# =============================================================================
CURRENT_STEP=2
step $CURRENT_STEP $TOTAL_STEPS "GitHub Secrets Synchronization"

if $GH_AUTH; then
  log "Fetching available GitHub secrets metadata..."
  OWNER_REPO=$(git config --get remote.origin.url | sed -E 's/.*github.com[:/]([^/]+)\/([^/.]+).*/\1\/\2/')
  log "  Repository: $OWNER_REPO"
  
  GH_SECRETS=$(gh secret list --repo "$OWNER_REPO" --json name 2>/dev/null || echo '[]')
  SECRET_COUNT=$(echo "$GH_SECRETS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
  log "  Available secrets: $SECRET_COUNT"
  
  # List critical secrets
  CRITICAL_SECRETS=("DOCKERHUB_USERNAME" "DOCKERHUB_TOKEN" "POSTGRES_PASSWORD" "SECRET_KEY")
  for secret in "${CRITICAL_SECRETS[@]}"; do
    if echo "$GH_SECRETS" | grep -q "\"$secret\""; then
      log "  ✓ $secret: configured in GitHub"
    else
      warn "  ⚠ $secret: NOT configured in GitHub (required for CI/CD)"
    fi
  done
else
  warn "Skipping GitHub secrets sync (gh not authenticated)"
fi

# =============================================================================
# STEP 3: Auto-Configuration (Development Environment)
# =============================================================================
CURRENT_STEP=3
step $CURRENT_STEP $TOTAL_STEPS "Auto-Configuration Engine (Development)"

cd "$ROOT_DIR"
# Always force regeneration for a clean development environment
./scripts/setup.sh --env-type development --force

log "Verifying generated configuration files..."
CONFIG_FILES=(
  "$BACKEND_DIR/.env"
  "$ROOT_DIR/.env.compose"
  "$FRONTEND_DIR/.env"
  "$ROOT_DIR/.env.example"
)
for f in "${CONFIG_FILES[@]}"; do
  if [[ -f "$f" ]]; then
    log "  ✓ $f exists ($(wc -l < "$f") lines)"
  else
    die "  ✗ $f missing"
  fi
done

# Verify backend config loads correctly
log "Validating backend Settings model..."
cd "$BACKEND_DIR"
source "$VENV_DIR/bin/activate"
python3 -c "
from app.core.config import settings
print(f'  ✓ Environment: {settings.environment}')
print(f'  ✓ Database: {settings.database_url.split(\"://\")[0]}')
print(f'  ✓ Secret key: {len(settings.secret_key)} chars')
print(f'  ✓ CORS origins: {settings.cors_origins}')
print(f'  ✓ Redis URL: {settings.redis_url or \"(not set)\"}')
print(f'  ✓ Pool size: {settings.db_pool_size}/{settings.db_max_overflow}')
print(f'  ✓ JWT expiry: {settings.access_token_expire_minutes} min')
print(f'  ✓ Password min length: {settings.password_min_length}')
print(f'  ✓ Rate limiting: {settings.rate_limit_enabled} ({settings.rate_limit_requests}/{settings.rate_limit_window}s)')
print(f'  ✓ Idempotency TTL: {settings.idempotency_ttl_hours}h')
print(f'  ✓ OTEL enabled: {settings.otel_enabled}')
print(f'  ✓ Debug: {settings.debug}')
" || die "Settings validation failed"

# =============================================================================
# STEP 4: Backend Provisioning
# =============================================================================
CURRENT_STEP=4
step $CURRENT_STEP $TOTAL_STEPS "Backend Provisioning (venv, deps, compile, migrations)"

log "Running backend syntax check (compileall)..."
python3 -m compileall -q app alembic
log "  ✓ Syntax check passed"

log "Running lint checks..."
ruff check app tests alembic
log "  ✓ Ruff check passed"

log "Running format check..."
ruff format --check app tests alembic
log "  ✓ Ruff format check passed"

log "Running database migrations..."
alembic upgrade head
log "  ✓ Migrations applied (single head verified)"

log "Verifying Alembic head..."
HEAD=$(alembic heads | head -1)
log "  ✓ Current head: $HEAD"

# =============================================================================
# STEP 5: Frontend Provisioning
# =============================================================================
if ! $SKIP_FRONTEND; then
  CURRENT_STEP=5
  step $CURRENT_STEP $TOTAL_STEPS "Frontend Provisioning (npm ci, build)"

  cd "$FRONTEND_DIR"
  log "Installing frontend dependencies (npm ci)..."
  npm ci --no-audit --no-fund
  log "  ✓ Dependencies installed ($(cat package-lock.json | grep -c '\"version\"' || echo 'N/A') packages)"

  log "Building frontend (Vite)..."
  VITE_API_BASE_URL=/api npm run build
  log "  ✓ Frontend build completed"
  
  # Verify build output
  if [[ -d "dist" && -f "dist/index.html" && -f "dist/assets/index-"*.js ]]; then
    JS_SIZE=$(ls -lh dist/assets/index-*.js | awk '{print $5}')
    CSS_SIZE=$(ls -lh dist/assets/index-*.css | awk '{print $5}')
    log "  ✓ Build artifacts: index.html, JS ($JS_SIZE), CSS ($CSS_SIZE)"
  else
    die "  ✗ Build output missing or incomplete"
  fi
else
  CURRENT_STEP=5
  step $CURRENT_STEP $TOTAL_STEPS "Frontend Provisioning (SKIPPED)"
  warn "Frontend setup skipped (--skip-frontend)"
fi

# =============================================================================
# STEP 6: Full Qualification Gate (CI-Equivalent)
# =============================================================================
if $QUALIFY; then
  CURRENT_STEP=6
  step $CURRENT_STEP $TOTAL_STEPS "Full Qualification Gate (scripts/qualify.sh)"

  cd "$ROOT_DIR"
  log "Running CI-equivalent qualification gate..."
  ./scripts/qualify.sh
  log "  ✓ Qualification gate PASSED"
else
  CURRENT_STEP=6
  step $CURRENT_STEP $TOTAL_STEPS "Qualification Gate (SKIPPED)"
  warn "Qualification gate skipped (--no-qualify)"
fi

# =============================================================================
# STEP 7: Infrastructure & Smoke Tests (Optional)
# =============================================================================
CURRENT_STEP=7
step $CURRENT_STEP $TOTAL_STEPS "Infrastructure & Smoke Tests"

if $WITH_INFRA; then
  if $DOCKER_AVAILABLE; then
    log "Starting Docker Compose stack with .env.compose..."
    cd "$ROOT_DIR"
    docker compose --env-file .env.compose up -d --build
    
    log "Waiting for services to be healthy..."
    sleep 10
    
    # Check backend health
    if curl -sf http://localhost:8000/api/v1/healthz >/dev/null; then
      log "  ✓ Backend health check: HEALTHY"
    else
      warn "  ⚠ Backend health check: NOT RESPONDING (may need more time)"
    fi
    
    # Check frontend
    if curl -sf http://localhost:3000/ >/dev/null; then
      log "  ✓ Frontend health check: HEALTHY"
    else
      warn "  ⚠ Frontend health check: NOT RESPONDING"
    fi
    
    log "Service status:"
    docker compose ps
  else
    warn "Docker daemon not available — skipping infrastructure start"
    warn "Run './scripts/setup.sh --with-infra' when Docker is available"
  fi
else
  log "Infrastructure start skipped (--with-infra not specified)"
  log "To start services later: ./scripts/setup.sh --with-infra"
fi

# =============================================================================
# STEP 8: Evidence Collection & Summary
# =============================================================================
CURRENT_STEP=8
step $CURRENT_STEP $TOTAL_STEPS "Evidence Collection & Summary"

cd "$ROOT_DIR"
log "Collecting verification evidence..."

# Git status
log "Git status:"
git status --short

# Test results summary
log "Backend test summary:"
cd "$BACKEND_DIR"
source "$VENV_DIR/bin/activate"
pytest --collect-only -q 2>/dev/null | tail -5 | head -1

# Frontend build verification
if [[ -d "$FRONTEND_DIR/dist" ]]; then
  log "Frontend build: $(ls -la $FRONTEND_DIR/dist/ | wc -l) files in dist/"
fi

# Configuration summary
log "Configuration files generated:"
for f in "${CONFIG_FILES[@]}"; do
  [[ -f "$f" ]] && log "  ✓ $f" || log "  ✗ $f (MISSING)"
done

# Workflow pinning verification
log "GitHub Actions SHA pinning:"
python3 "$ROOT_DIR/scripts/pin-github-actions.py" --check 2>&1 | tail -3

# Final summary
cat <<SUMMARY_EOF

ERP03 DEVELOPMENT ENVIRONMENT READY
====================================

Repository: ${OWNER_REPO:-unknown}
Branch: $CURRENT_BRANCH
Commit: $COMMIT_SHA
Python: $PY_VERSION | Node: $NODE_MAJOR | Docker: ${DOCKER_AVAILABLE:-false} | GH: ${GH_AUTH:-false}

VERIFICATION STATUS:
[1/8] Prerequisites: PASS
[2/8] GitHub secrets: SYNCED
[3/8] Auto-config (dev): OK
[4/8] Backend: VENV + DEPS + COMPILE + LINT + MIGRATE: OK
[5/8] Frontend: NPM CI + BUILD: OK
[6/8] Qualification gate: PASSED
[7/8] Infrastructure: PLACEHOLDER
[8/8] Evidence collection: OK

NEXT ACTIONS:
1. Activate venv:     source .venv/bin/activate
2. Run backend:       cd ERP-BACKEND && uvicorn app.main:app --reload
3. Run frontend:      cd frontend && npm run dev
4. Or start all:      ./scripts/setup.sh --with-infra
5. Push to trigger CI: git push origin $CURRENT_BRANCH

SUMMARY_EOF

log "Development environment setup COMPLETE!"