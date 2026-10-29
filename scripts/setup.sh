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
# ---------------------------------------------------------------------------
check_gh_auth() {
  local PKG="${PKG:-$(command -v apt >/dev/null && echo apt || command -v brew >/dev/null && echo brew || command -v choco >/dev/null && echo choco || echo 'package-manager')}"
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
    token_urlsafe* ) local n="${spec#token_urlsafe(}"; n="${n%)}"; "$VENV_DIR/bin/python" -c "import secrets; print(secrets.token_urlsafe($n))" 2>/dev/null || python3 -c "import secrets; print(secrets.token_urlsafe($n))" ;;
    token_hex* ) local n="${spec#token_hex(}"; n="${n%)}"; head -c "$n" /dev/urandom | od -An -tx1 | tr -d ' \n' ;;
    default:* ) echo "${spec#default:}" ;;
    fixed:* ) echo "${spec#fixed:}" ;;
    from_github ) echo "" ;;  # placeholder, filled from GitHub if available
    * ) echo "$spec" ;;
  esac
}

# Derive GitHub owner/repo from git remote
gh_owner_repo() {
  local url
  url="$(git -C "$ROOT_DIR" config --get remote.origin.url 2>/dev/null || echo "")"
  # Handle git@github.com:owner/repo.git or https://github.com/owner/repo.git
  if [[ "$url" =~ github.com[:/]([^/]+)/([^/.]+) ]]; then
    echo "${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
  else
    echo "nyeinpyaesone-ui/ERP03"  # fallback
  fi
}

sync_github_secrets() {
  log "Syncing GitHub secrets to local .env files..."
  check_gh_auth
  local owner_repo gh_secrets
  owner_repo="$(gh_owner_repo)"
  gh_secrets="$(gh secret list --repo "$owner_repo" --json name 2>/dev/null || echo '[]')"
  log "Available GitHub secrets: $(echo "$gh_secrets" | "$VENV_DIR/bin/python" -c "import sys, json; [print(x['name'], end=' ') for x in json.load(sys.stdin)]" 2>/dev/null || echo "jq not available")"
  log "Note: Secret values are not readable via GitHub API — they must be set in CI/CD environment"
}

auto_configure_all() {
  log "🔧 Auto-configuring environment ($ENV_TYPE)..."

  # 1. Ensure venv exists for secret generation
  if [[ ! -d "$VENV_DIR" ]]; then
    local py; py="$(python_cmd)"
    "$py" -m venv "$VENV_DIR"
  fi
  # Use venv pip directly (activation not reliable in script context)
  "$VENV_DIR/bin/pip" install --quiet --upgrade pip
  "$VENV_DIR/bin/pip" install --quiet -r "$BACKEND_DIR/requirements.txt"

  # 2. Generate ALL secret values dynamically
  declare -A SECRETS
  for name in "${!SECRET_SPECS[@]}"; do
    IFS='|' read -r desc generator required <<< "${SECRET_SPECS[$name]}"
    SECRETS[$name]="$(generate_secure_value "$generator")"
  done

  # 3. Try to pull values from GitHub secrets (for CI/production values)
  if $SYNC_SECRETS && check_gh_auth 2>/dev/null; then
    log "Fetching available secrets from GitHub..."
    local gh_secrets owner_repo
    owner_repo="$(gh_owner_repo)"
    gh_secrets="$(gh secret list --repo "$(gh_owner_repo)" --json name 2>/dev/null || echo '[]')"
    for name in "${!SECRET_SPECS[@]}"; do
      IFS='|' read -r desc generator required <<< "${SECRET_SPECS[$name]}"
      if [[ "$generator" == "from_github" ]] && echo "$gh_secrets" | grep -q "\"$name\""; then
        SECRETS[$name]="__GITHUB_SECRET__"
        log "  ✓ $name configured in GitHub (will be injected at runtime)"
      fi
    done
  fi

  # 4. Generate backend .env — essential fields only (matching Settings model)
  local backend_env="$BACKEND_DIR/.env"
  if [[ -f "$backend_env" && "$FORCE" != "true" ]]; then
    log "Keeping existing $backend_env (use --force to regenerate)"
  else
    log "Generating $backend_env..."
    mkdir -p "$BACKEND_DIR/.local"
    if [[ "$ENV_TYPE" == "development" ]]; then
      cat > "$backend_env" <<EOF
# ERP03 Backend Config — AUTO-GENERATED development
ENVIRONMENT=development
SECRET_KEY=${SECRETS[SECRET_KEY]}
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite+aiosqlite:///$ROOT_DIR/ERP-BACKEND/.local/erp03.sqlite3
DATABASE_PATH=$ROOT_DIR/ERP-BACKEND/.local/erp03.sqlite3
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=1800
DB_ECHO=false
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000
TYPESAFE_ENABLED=false
TYPESAFE_API_KEY=
JWT_EXPIRY_MINUTES=30
EOF
    else
      local db_host="${SECRETS[DB_HOST]:-localhost}"
      local db_pass="${SECRETS[DB_PASSWORD]}"
      # Ensure DB_PASSWORD is not empty for production
      if [[ -z "$db_pass" || "$db_pass" == "__GITHUB_SECRET__" ]]; then
        warn "DB_PASSWORD not set locally; generate a strong one or set in GitHub secrets"
        db_pass="$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
      fi
      cat > "$backend_env" <<EOF
# ERP03 Backend Config — AUTO-GENERATED production
ENVIRONMENT=production
SECRET_KEY=${SECRETS[SECRET_KEY]}
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://erp03:${db_pass}@${db_host}:5432/erp03
DATABASE_PATH=
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_RECYCLE=3600
DB_ECHO=false
CORS_ORIGINS=https://your-domain.com
TYPESAFE_ENABLED=true
TYPESAFE_API_KEY=
JWT_EXPIRY_MINUTES=15
EOF
    fi
    chmod 600 "$backend_env"
    log "  ✓ Backend config written"
  fi

  # 5. Generate frontend .env for Vite build (uses /api for nginx proxy)
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

  # 6. Verify configuration loads correctly
  log "Verifying configuration..."
  (cd "$BACKEND_DIR" && "$VENV_DIR/bin/python" -c "
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
  log "  • $frontend_env"
  log ""
  log "🚀 Ready to start:"
  log "  source .venv/bin/activate"
  log "  ./scripts/setup.sh --with-infra   # Start all services"
  log "  ./scripts/setup.sh --qualify      # Run full test gate"
}

# ---------------------------------------------------------------------------
# 4. Backend environment provisioning (legacy path)
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
# 5. Secure local configuration (.env) — legacy generator (fallback)
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
  (cd "$FRONTEND_DIR" && npm ci --no-audit --no-fund --silent)
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

  # Use auto_configure_all for full config generation; falls back to legacy path
  if [[ -f "$BACKEND_DIR/.env" && "$FORCE" != "true" ]]; then
    log "Using existing $BACKEND_DIR/.env (use --force to regenerate)"
    setup_backend
  else
    auto_configure_all
  fi

  setup_frontend

  # Run smoke test after full setup
  smoke_test

  if $WITH_INFRA; then start_infra; fi
  if $QUALIFY; then
    log "Running full qualification gate"
    bash "$ROOT_DIR/scripts/qualify.sh"
  fi
  log "ERP03 bootstrap complete ($PLATFORM). Activate the env with: source .venv/bin/activate"
}

main "$@"