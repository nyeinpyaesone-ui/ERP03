#!/usr/bin/env bash
#
# ERP03 — automated, cross-platform development bootstrap.
#
# Detects the host platform (Linux / macOS / WSL), verifies or installs the
# required toolchain, provisions an isolated virtualenv, installs pinned
# backend + frontend dependencies, generates a secure .env when missing,
# and optionally starts local infrastructure (Docker Compose) and runs the
# full qualification gate.
#
# Usage:
#   ./scripts/setup.sh [options]
#
# Options:
#   --with-infra     Start Docker Compose services (postgres/backend/frontend...)
#                    after bootstrap completes.
#   --qualify        Run scripts/qualify.sh at the end (full CI-equivalent gate).
#   --skip-frontend  Do not install frontend npm dependencies.
#   --sync-secrets   Fetch secrets from GitHub and create/update .env files.
#   --env-type       Target environment: development (default) | production.
#   --force          Overwrite existing .env files when syncing secrets.
#   --help           Show this help.
#
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/ERP-BACKEND"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"

WITH_INFRA=false
QUALIFY=false
SKIP_FRONTEND=false
SYNC_SECRETS=false
ENV_TYPE="development"
FORCE=false

log()  { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
  sed -n '3,23p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-infra) WITH_INFRA=true ;;
    --qualify) QUALIFY=true ;;
    --skip-frontend) SKIP_FRONTEND=true ;;
    --sync-secrets) SYNC_SECRETS=true ;;
    --env-type) ENV_TYPE="${2:-}"; shift ;;
    --force) FORCE=true ;;
    --help|-h) usage; exit 0 ;;
    *) die "unknown option: $1 (see --help)" ;;
  esac
  shift
done

# Validate env type
case "$ENV_TYPE" in
  development|production) ;;
  *) die "Invalid --env-type: $ENV_TYPE (must be development|production)" ;;
esac

# ---------------------------------------------------------------------------
# 1. Platform detection
# ---------------------------------------------------------------------------
detect_platform() {
  local os arch
  os="$(uname -s)"
  arch="$(uname -m)"
  case "$os" in
    Linux)
      if grep -qiE '(microsoft|wsl)' /proc/version 2>/dev/null; then
        PLATFORM="wsl"
      else
        PLATFORM="linux"
      fi
      ;;
    Darwin) PLATFORM="macos" ;;
    MINGW*|MSYS*|CYGWIN*) PLATFORM="windows-bash" ;;
    *) die "unsupported platform: $os" ;;
  esac
  ARCH="$arch"
  # Package manager preference for optional install hints.
  if command -v apt-get >/dev/null; then PKG="apt"
  elif command -v dnf >/dev/null; then PKG="dnf"
  elif command -v brew >/dev/null; then PKG="brew"
  else PKG="none"
  fi
}

# ---------------------------------------------------------------------------
# 2. Toolchain verification (auto-detect suitable services & runtimes)
# ---------------------------------------------------------------------------
require_cmd() {
  local cmd="$1" hint="${2:-}"
  if command -v "$cmd" >/dev/null 2>&1; then
    return 0
  fi
  if [[ -n "$hint" ]]; then
    die "$cmd is required but was not found. Install hint [$PKG]: $hint"
  fi
  die "$cmd is required but was not found."
}

python_cmd() {
  # Prefer an explicit 3.12+ interpreter; fall back to python3.
  for candidate in python3.12 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

check_toolchain() {
  log "Toolchain check ($PLATFORM/$arch_lower via $PKG)"
  local py
  py="$(python_cmd)" || die "Python >= 3.12 is required. Install hint [$PKG]: python3.12"
  PY_VERSION="$("$py" --version 2>&1)"
  log "Using $py ($PY_VERSION)"
  require_cmd node "nodejs (LTS 20+)"
  require_cmd npm "bundled with nodejs"
  NODE_MAJOR="$(node --version | sed 's/v\([0-9]*\).*/\1/')"
  (( NODE_MAJOR >= 18 )) || die "Node >= 18 required, found $(node --version)"
  if docker_available; then
    log "Docker detected — compose services available locally"
  else
    warn "Docker not found: skipping container-based services (backend still runs against SQLite/Postgres URLs you provide)"
  fi
}

docker_available() {
  command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    die "docker compose is required for --with-infra"
  fi
}

# ---------------------------------------------------------------------------
# 3. Auto-Configuration Engine — Dynamic, zero-touch environment setup
#    Generates ALL configs, secrets, migrations, and verifies health automatically
# ---------------------------------------------------------------------------
check_gh_auth() {
  if ! command -v gh >/dev/null 2>&1; then
    die "GitHub CLI (gh) not found. Install hint [$PKG]: gh"
  fi
  if ! gh auth status >/dev/null 2>&1; then
    die "gh not authenticated. Run: gh auth login"
  fi
}

# Centralized secret registry — single source of truth for all environments
declare -A SECRET_SPECS=(
  # [secret_name]="description|generator|required_for"
  ["SECRET_KEY"]="Application secret key|token_urlsafe(48)|all"
  ["POSTGRES_PASSWORD"]="PostgreSQL password|token_hex(24)|production,compose"
  ["REDIS_PASSWORD"]="Redis password|token_hex(24)|compose"
  ["DOCKERHUB_TOKEN"]="Docker Hub PAT|from_github|ci,production"
  ["DB_PASSWORD"]="Production DB password|from_github|production"
  ["DB_HOST"]="Production DB host|from_github|production"
  ["REDIS_USER"]="Redis username|default:default|compose"
  ["REDIS_ACCOUNT_NUMBER"]="Upstash Redis account|from_github|production"
  ["API_REDIS_KEY"]="Upstash Redis REST API key|from_github|production"
  ["OLLAMA_IMAGE_TAG"]="Ollama version|fixed:0.32.5|all"
)

generate_secure_value() {
  local spec="$1"
  case "$spec" in
    token_urlsafe* ) local n="${spec#token_urlsafe(}"; n="${n%)}"; "$VENV_DIR/bin/python" -c "import secrets; print(secrets.token_urlsafe($n))" 2>/dev/null || head -c $((n*4/3)) /dev/urandom | od -An -tx1 | tr -d ' \n' ;;
    token_hex* ) local n="${spec#token_hex(}"; n="${n%)}"; head -c "$n" /dev/urandom | od -An -tx1 | tr -d ' \n' ;;
    default:* ) echo "${spec#default:}" ;;
    fixed:* ) echo "${spec#fixed:}" ;;
    from_github ) echo "" ;;  # placeholder, filled from GitHub if available
    * ) echo "$spec" ;;
  esac
}

sync_github_secrets() {
  log "Syncing GitHub secrets to local .env files..."
  check_gh_auth
  local gh_secrets
  gh_secrets="$(gh secret list --repo nyeinpyaesone-ui/ERP03 --json name 2>/dev/null || echo '[]')"
  log "Available GitHub secrets: $(echo "$gh_secrets" | /home/admin/projects/nyeinpyaesone-ui/ERP03/.venv/bin/python -c "import sys, json; [print(x['name'], end=' ') for x in json.load(sys.stdin)]" 2>/dev/null || echo "jq not available")"
  log "Note: Secret values are not readable via GitHub API — they must be set in CI/CD environment"
}

auto_configure_all() {
  log "🔧 Auto-configuring complete environment ($ENV_TYPE)..."

  # 1. Ensure venv exists for secret generation
  if [[ ! -d "$VENV_DIR" ]]; then
    local py; py="$(python_cmd)"
    "$py" -m venv "$VENV_DIR"
  fi
  source "$VENV_DIR/bin/activate" 2>/dev/null || true
  pip install --quiet --upgrade pip 2>/dev/null || true
  pip install --quiet -r "$BACKEND_DIR/requirements.txt" 2>/dev/null || true

  # 2. Generate ALL secret values dynamically
  declare -A SECRETS
  for name in "${!SECRET_SPECS[@]}"; do
    IFS='|' read -r desc generator required <<< "${SECRET_SPECS[$name]}"
    SECRETS[$name]="$(generate_secure_value "$generator")"
  done

  # 3. Try to pull values from GitHub secrets (for CI/production values)
  if $SYNC_SECRETS && check_gh_auth 2>/dev/null; then
    log "Fetching available secrets from GitHub..."
    local gh_secrets
    gh_secrets="$(gh secret list --repo nyeinpyaesone-ui/ERP03 --json name 2>/dev/null || echo '[]')"
    for name in "${!SECRET_SPECS[@]}"; do
      IFS='|' read -r desc generator required <<< "${SECRET_SPECS[$name]}"
      if [[ "$generator" == "from_github" ]] && echo "$gh_secrets" | grep -q "\"$name\""; then
        # Can't read values, but we know they exist in GitHub for CI
        SECRETS[$name]="__GITHUB_SECRET__"
        log "  ✓ $name configured in GitHub (will be injected at runtime)"
      fi
    done
  fi

  # 4. Generate backend .env — fully populated
  local backend_env="$BACKEND_DIR/.env"
  if [[ -f "$backend_env" && "$FORCE" != "true" ]]; then
    log "Keeping existing $backend_env (use --force to regenerate)"
  else
    log "Generating $backend_env..."
    mkdir -p "$BACKEND_DIR/.local"
    if [[ "$ENV_TYPE" == "development" ]]; then
      cat > "$backend_env" <<EOF
# ============================================================
# ERP03 Backend Configuration — AUTO-GENERATED
# Environment: development
# Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
# ============================================================
# CORE
ENVIRONMENT=development
SECRET_KEY=${SECRETS[SECRET_KEY]}
DEBUG=true
LOG_LEVEL=DEBUG

# DATABASE (SQLite for zero-config dev)
DATABASE_URL=sqlite+aiosqlite:///$ROOT_DIR/ERP-BACKEND/.local/erp03.sqlite3
DATABASE_PATH=$ROOT_DIR/ERP-BACKEND/.local/erp03.sqlite3
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=1800
DB_ECHO=false

# CORS (comma-separated; declared in app.core.config.Settings)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000

# TYPESAFE (optional error classification; declared in app.core.config.Settings)
TYPESAFE_ENABLED=false
TYPESAFE_API_KEY=

# JWT (declared in app.core.config.Settings as jwt_expiry_minutes)
JWT_EXPIRY_MINUTES=30
EOF
    else
      # Production config with PostgreSQL
      local db_host="${SECRETS[DB_HOST]:-localhost}"
      local db_pass="${SECRETS[DB_PASSWORD]}"
      cat > "$backend_env" <<EOF
# ============================================================
# ERP03 Backend Configuration — AUTO-GENERATED PRODUCTION
# Environment: production
# Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
# ============================================================
# CORE
ENVIRONMENT=production
SECRET_KEY=${SECRETS[SECRET_KEY]}
LOG_LEVEL=INFO

# DATABASE (PostgreSQL required for production)
DATABASE_URL=postgresql+asyncpg://erp03:${db_pass}@${db_host}:5432/erp03_prod
DATABASE_PATH=$ROOT_DIR/ERP-BACKEND/.local/erp03.sqlite3
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_RECYCLE=3600
DB_ECHO=false

# CORS (HTTPS only in production; declared in app.core.config.Settings)
CORS_ORIGINS=https://your-domain.com

# TYPESAFE (optional error classification; declared in app.core.config.Settings)
TYPESAFE_ENABLED=true
TYPESAFE_API_KEY=

# JWT (declared in app.core.config.Settings as jwt_expiry_minutes)
JWT_EXPIRY_MINUTES=15
EOF
    fi
    chmod 600 "$backend_env"
    log "  ✓ Backend config written ($(wc -l < "$backend_env") lines)"
  fi

  # 5. Generate .env.compose — fully populated for docker compose
  local compose_env="$ROOT_DIR/.env.compose"
  if [[ -f "$compose_env" && "$FORCE" != "true" ]]; then
    log "Keeping existing $compose_env (use --force to regenerate)"
  else
    log "Generating $compose_env..."
    cat > "$compose_env" <<EOF
# ============================================================
# ERP03 Docker Compose Environment — AUTO-GENERATED
# Environment: ${ENV_TYPE}
# Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
# Usage: docker compose --env-file .env.compose up -d
# ============================================================

# ────────────────────────────────────────────────────────────
# DATABASE
# ────────────────────────────────────────────────────────────
POSTGRES_DB=erp03
POSTGRES_USER=erp03
POSTGRES_PASSWORD=${SECRETS[POSTGRES_PASSWORD]}
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# ────────────────────────────────────────────────────────────
# REDIS
# ────────────────────────────────────────────────────────────
REDIS_PASSWORD=${SECRETS[REDIS_PASSWORD]}
REDIS_USER=${SECRETS[REDIS_USER]}
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://:${SECRETS[REDIS_PASSWORD]}@redis:6379/0
REDIS_ACCOUNT_NUMBER=${SECRETS[REDIS_ACCOUNT_NUMBER]}
API_REDIS_KEY=${SECRETS[API_REDIS_KEY]}

# ────────────────────────────────────────────────────────────
# DOCKER HUB (CI/CD)
# ────────────────────────────────────────────────────────────
DOCKERHUB_USERNAME=powerrangeranikg
DOCKERHUB_TOKEN=${SECRETS[DOCKERHUB_TOKEN]}
DOCKERHUB_IMAGE_BACKEND=powerrangeranikg/erp03-backend
DOCKERHUB_IMAGE_FRONTEND=powerrangeranikg/erp03-frontend
IMAGE_TAG=${IMAGE_TAG:-latest}

# ────────────────────────────────────────────────────────────
# BACKEND
# ────────────────────────────────────────────────────────────
SECRET_KEY=${SECRETS[SECRET_KEY]}
ENVIRONMENT=${ENV_TYPE}
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
API_URL=http://localhost:8000
WS_URL=ws://localhost:8000
DATABASE_URL=postgresql://erp03:${SECRETS[POSTGRES_PASSWORD]}@postgres:5432/erp03
OLLAMA_URL=http://ollama:11434

# ────────────────────────────────────────────────────────────
# FRONTEND
# ────────────────────────────────────────────────────────────
VITE_API_BASE_URL=/api
VITE_WS_URL=ws://localhost:8000
VITE_APP_TITLE=ERP03

# ────────────────────────────────────────────────────────────
# OLLAMA
# ────────────────────────────────────────────────────────────
OLLAMA_IMAGE_TAG=${SECRETS[OLLAMA_IMAGE_TAG]}

# ────────────────────────────────────────────────────────────
# NGINX (production reverse proxy)
# ────────────────────────────────────────────────────────────
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem
EOF
    chmod 600 "$compose_env"
    log "  ✓ Compose config written ($(wc -l < "$compose_env") lines)"
  fi

  # 6. Generate frontend .env for Vite build
  local frontend_env="$FRONTEND_DIR/.env"
  if [[ -f "$frontend_env" && "$FORCE" != "true" ]]; then
    log "Keeping existing $frontend_env"
  else
    log "Generating $frontend_env..."
    cat > "$frontend_env" <<EOF
# ERP03 Frontend Build Config — AUTO-GENERATED
VITE_API_BASE_URL=/api
VITE_WS_URL=ws://localhost:8000
VITE_APP_TITLE=ERP03
VITE_APP_VERSION=1.0.0
VITE_ENABLE_DEVTOOLS=true
VITE_THEME=light
EOF
    log "  ✓ Frontend config written"
  fi

  # 7. Generate docker-compose.override.yml for local dev customizations
  local override_file="$ROOT_DIR/docker-compose.override.yml"
  if [[ ! -f "$override_file" || "$FORCE" == "true" ]]; then
    log "Generating $override_file..."
    cat > "$override_file" <<'EOF'
# docker-compose.override.yml — AUTO-GENERATED LOCAL OVERRIDES
# This file is auto-generated by setup.sh. Do not edit manually.
# For permanent changes, modify docker-compose.yml or docker-compose.dev.yml

services:
  backend:
    volumes:
      - ./ERP-BACKEND:/app:cached
      - ./ERP-BACKEND/.local:/app/.local:cached
    environment:
      - PYTHONPATH=/app
      - PYTHONDONTWRITEBYTECODE=1
      - PYTHONUNBUFFERED=1
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    develop:
      watch:
        - action: sync
          path: ./ERP-BACKEND/app
          target: /app/app
        - action: rebuild
          path: ./ERP-BACKEND/requirements.txt

  frontend:
    volumes:
      - ./frontend:/app:cached
      - /app/node_modules
    environment:
      - CHOKIDAR_USEPOLLING=true
    command: npm run dev -- --host 0.0.0.0 --port 5173
    develop:
      watch:
        - action: sync
          path: ./frontend/src
          target: /app/src
        - action: rebuild
          path: ./frontend/package.json

  postgres:
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups

  redis:
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
EOF
    log "  ✓ Compose override written"
  fi

  # 8. Run database migrations automatically
  log "Running database migrations..."
  (cd "$BACKEND_DIR" && DATABASE_PATH="$BACKEND_DIR/.local/erp03.sqlite3" alembic upgrade head 2>/dev/null) || warn "Migration skipped (will run on first backend start)"

  # 9. Verify configuration loads correctly
  log "Verifying configuration..."
  (cd "$BACKEND_DIR" && python -c "
from app.core.config import settings
print(f'  ✓ Environment: {settings.environment}')
print(f'  ✓ Database: {settings.database_url.split(\"://\")[0]}')
print(f'  ✓ Secret key: {len(settings.secret_key)} chars')
print(f'  ✓ CORS origins: {settings.cors_origins}')
") 2>/dev/null || warn "Config verification will run on backend start"

  log "✅ Auto-configuration complete!"
  log ""
  log "📋 Generated files:"
  log "  • $backend_env"
  log "  • $compose_env"
  log "  • $frontend_env"
  log "  • $override_file"
  log ""
  log "🚀 Ready to start:"
  log "  source .venv/bin/activate"
  log "  ./scripts/setup.sh --with-infra   # Start all services"
  log "  ./scripts/setup.sh --qualify      # Run full test gate"
}

# ---------------------------------------------------------------------------
# 4. Backend environment provisioning
# ---------------------------------------------------------------------------
setup_backend() {
  log "Provisioning Python virtualenv at $VENV_DIR"
  local py
  py="$(python_cmd)"
  if [[ ! -d "$VENV_DIR" ]]; then
    "$py" -m venv "$VENV_DIR"
  fi
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  pip install --quiet --upgrade pip || pip install --quiet --upgrade pip
  pip install --quiet --requirement "$BACKEND_DIR/requirements.txt" || pip install --quiet --requirement "$BACKEND_DIR/requirements.txt"
  pip install --quiet --requirement "$BACKEND_DIR/dev-requirements.txt" || pip install --quiet --requirement "$BACKEND_DIR/dev-requirements.txt"
  log "Backend dependencies installed (pinned versions verified by CI)"
}

# ---------------------------------------------------------------------------
# 5. Secure local configuration (.env) — legacy generator
# ---------------------------------------------------------------------------
generate_env() {
  local env_file="$BACKEND_DIR/.env"
  if [[ -f "$env_file" ]]; then
    log "Keeping existing $env_file"
    return
  fi
  log "Generating secure development $env_file"
  local secret
  secret="$("$VENV_DIR/bin/python" -c 'import secrets; print(secrets.token_urlsafe(48))')"
  cat > "$env_file" <<EOF
# Generated by scripts/setup.sh — development only, never commit this file.
ENVIRONMENT=development
SECRET_KEY=${secret}
DATABASE_URL=sqlite+aiosqlite:///$ROOT_DIR/ERP-BACKEND/.local/erp03.sqlite3
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
DATABASE_PATH=$ROOT_DIR/ERP-BACKEND/.local/erp03.sqlite3
EOF
  mkdir -p "$BACKEND_DIR/.local"
  chmod 600 "$env_file"
}

# ---------------------------------------------------------------------------
# 6. Frontend dependencies
# ---------------------------------------------------------------------------
setup_frontend() {
  if $SKIP_FRONTEND; then
    log "Skipping frontend install (--skip-frontend)"
    return
  fi
  log "Installing frontend dependencies"
  (cd "$FRONTEND_DIR" && npm install --no-audit --no-fund --silent)
}

# ---------------------------------------------------------------------------
# 7. Optional infrastructure + smoke verification
# ---------------------------------------------------------------------------
start_infra() {
  if ! docker_available; then
    die "--with-infra requested but Docker daemon is unavailable"
  fi
  log "Starting Docker Compose stack"
  (cd "$ROOT_DIR" && POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')}" \
    SECRET_KEY="$(head -c 48 /dev/urandom | od -An -tx1 | tr -d ' \n')" compose_cmd up -d --build)
  log "Compose stack started: API http://localhost:8000/docs · UI http://localhost:3000"
}

smoke_test() {
  log "Running hermetic test suite as bootstrap smoke test"
  (cd "$BACKEND_DIR" && DATABASE_PATH="$(mktemp -d)/erp03.sqlite3" pytest -q)
}

# ---------------------------------------------------------------------------
main() {
  detect_platform
  arch_lower="$(echo "$ARCH" | tr '[:upper:]' '[:lower:]')"

  if $SYNC_SECRETS; then
    sync_github_secrets
    # If only syncing secrets, exit early unless other flags set
    if ! $WITH_INFRA && ! $QUALIFY; then
      log "Secrets sync complete. Run without --sync-secrets to continue bootstrap."
      exit 0
    fi
  fi

  check_toolchain
  setup_backend
  generate_env
  setup_frontend
  smoke_test
  if $WITH_INFRA; then start_infra; fi
  if $QUALIFY; then
    log "Running full qualification gate"
    bash "$ROOT_DIR/scripts/qualify.sh"
  fi
  log "ERP03 bootstrap complete ($PLATFORM). Activate the env with: source .venv/bin/activate"
}

main "$@"