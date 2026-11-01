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
#   --sync-secrets   Sync GitHub secrets availability (values not readable via API).
#   --env-type       Target environment: development (default) | staging | production.
#   --force          Overwrite existing .env files when regenerating.
#   --skip-preflight Do not run the pre-configuration check before installing.
#                    (Preflight runs automatically and blocks installs on
#                    unmet hard requirements.)
#   --preflight-only Run only the pre-configuration check, then exit 0/1.
#   --help           Show this help.
#
# Requirements satisfied by this script:
#   * Python >= 3.12, Node >= 20.19 (Vite 7), git; Docker optional (only for
#     --with-infra / compose-based services).
#   * Pinned backend deps: ERP-BACKEND/requirements.txt + dev-requirements.txt
#     installed into an isolated virtualenv ($VENV_DIR, default ./.venv).
#   * Frontend deps: frontend/package-lock.json honoured via `npm ci`.
#   * Generated configs: ERP-BACKEND/.env (fields MUST match the Settings model
#     in app/core/config.py — extra="forbid"), .env.compose, frontend/.env,
#     .env.example. Existing files are kept unless --force.
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
  awk 'NR>=3 && /^set -Eeuo/{exit} NR>=3 && /^#/{sub(/^# ?/,""); print}' "${BASH_SOURCE[0]}"
}

WITH_PREFLIGHT=true
PREFLIGHT_ONLY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-infra) WITH_INFRA=true ;;
    --qualify) QUALIFY=true ;;
    --skip-frontend) SKIP_FRONTEND=true ;;
    --sync-secrets) SYNC_SECRETS=true ;;
    --env-type) ENV_TYPE="${2:-}"; shift ;;
    --force) FORCE=true ;;
    --skip-preflight) WITH_PREFLIGHT=false ;;
    --preflight-only) PREFLIGHT_ONLY=true ;;
    --help|-h) usage; exit 0 ;;
    *) die "unknown option: $1 (see --help)" ;;
  esac
  shift
done

# Validate env type
case "$ENV_TYPE" in
  development|staging|production) ;;
  *) die "Invalid --env-type: $ENV_TYPE (must be development|staging|production)" ;;
esac

# Backend pool sizing written into ERP-BACKEND/.env per tier. The Settings
# model also auto-tunes, but the generated file must state explicit values.
case "$ENV_TYPE" in
  production)   POOL_SIZE=20; POOL_OVERFLOW=30; POOL_RECYCLE=3600 ;;
  staging)      POOL_SIZE=10; POOL_OVERFLOW=30; POOL_RECYCLE=1800 ;;
  *)            POOL_SIZE=5;  POOL_OVERFLOW=10; POOL_RECYCLE=900  ;;
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
  require_cmd git "git (e.g. apt: git | brew: git)"
  require_cmd node "nodejs (LTS 20.19+; CI uses 22)"
  require_cmd npm "bundled with nodejs"
  # Vite 7 requires Node >= 20.19 — same floor as scripts/agent/bootstrap.sh.
  NODE_MAJOR="$(node --version | sed 's/v\([0-9]*\).*/\1/')"
  NODE_MINOR="$(node --version | sed 's/v[0-9]*\.\([0-9]*\).*/\1/')"
  if (( NODE_MAJOR < 20 )) || { (( NODE_MAJOR == 20 )) && (( NODE_MINOR < 19 )); }; then
    die "Node >= 20.19 required (Vite 7), found $(node --version)"
  fi
  if ! docker_available; then
    warn "Docker not found: skipping container-based services (backend still runs against SQLite/Postgres URLs you provide)"
  fi
}

docker_available() {
  command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

# ---------------------------------------------------------------------------
# 2b. Pre-configuration check — accurate, version-specific gate that runs
#     BEFORE any install trigger (venv creation, pip/npm pulls). It compares
#     the host toolchain against the pinned compatibility matrix below and
#     exits non-zero on any hard-requirement miss, so setup never half-
#     installs against an incompatible runtime. Optional components are
#     reported as warnings with the exact flag they block.
# ---------------------------------------------------------------------------
# Compatibility matrix (single source of truth for preflight; keep in sync
# with scripts/agent/bootstrap.sh and CI workflow images):
REQ_PYTHON="3.12"
REQ_NODE="20.19"          # Vite 7 engine floor; CI uses Node 22 LTS
REQ_GIT="2.30"
REQ_NPM="10"              # bundled with Node >= 20
REQ_COMPOSE_FILE="docker-compose.yml"

ver_ge() {  # ver_ge "20.19.2" "20.19" -> true ; tolerates suffixes like 1.2.3-rc1
  local IFS=.
  # shellcheck disable=SC2086
  local a=(${1:-0}) b=(${2:-0}) i x y
  for i in 0 1 2; do
    x="${a[i]:-0}"; x="${x%%[!0-9]*}"; x="${x:-0}"
    y="${b[i]:-0}"; y="${y%%[!0-9]*}"; y="${y:-0}"
    if (( x > y )); then return 0; fi
    if (( x < y )); then return 1; fi
  done
  return 0
}

preflight_check() {
  log "Pre-configuration check (compatibility gate before installs)"
  local errors=0 warnings=0

  report() {  # report OK|WARN|FAIL label detail
    case "$1" in
      OK)   printf '  \033[0;32m✔\033[0m %-42s %s\n' "$2" "$3" ;;
      WARN) printf '  \033[1;33m⚠\033[0m %-42s %s\n' "$2" "$3"; warnings=$((warnings+1)) ;;
      FAIL) printf '  \033[1;31m✘\033[0m %-42s %s\n' "$2" "$3"; errors=$((errors+1)) ;;
    esac
  }

  # --- Python interpreter (hard requirement) ---
  local py py_ver=""
  if py="$(python_cmd)"; then
    py_ver="$("$py" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])')"
    if ver_ge "${py_ver%.*}" "$REQ_PYTHON"; then
      report OK "python ($py)" "$py_ver >= $REQ_PYTHON"
    else
      report FAIL "python ($py)" "$py_ver < $REQ_PYTHON"
    fi
  else
    report FAIL "python >= $REQ_PYTHON" "no 3.12+ interpreter found (python3.12/python3/python)"
  fi

  # --- git (hard requirement: venv tooling, evidence commits, hooks) ---
  if command -v git >/dev/null 2>&1; then
    local git_ver; git_ver="$(git --version | awk '{print $3}')"
    ver_ge "$git_ver" "$REQ_GIT" \
      && report OK "git" "$git_ver >= $REQ_GIT" \
      || report FAIL "git" "$git_ver < $REQ_GIT"
  else
    report FAIL "git >= $REQ_GIT" "not installed"
  fi

  # --- Node + npm (hard requirement for frontend; Vite 7 engine floor) ---
  if command -v node >/dev/null 2>&1; then
    local node_ver
    node_ver="$(node --version | sed 's/^v//')"
    if ver_ge "$node_ver" "$REQ_NODE"; then
      report OK "node" "$node_ver >= $REQ_NODE (Vite 7)"
    else
      report FAIL "node" "$node_ver < $REQ_NODE (Vite 7 requires 20.19+)"
    fi
  elif $SKIP_FRONTEND; then
    report WARN "node" "not installed; acceptable with --skip-frontend"
  else
    report FAIL "node >= $REQ_NODE" "not installed (required by frontend build)"
  fi

  if command -v npm >/dev/null 2>&1; then
    local npm_ver; npm_ver="$(npm --version)"
    ver_ge "$npm_ver" "$REQ_NPM" \
      && report OK "npm" "$npm_ver >= $REQ_NPM" \
      || { $SKIP_FRONTEND && report WARN "npm" "$npm_ver < $REQ_NPM (older npm usually still works)" \
           || report FAIL "npm" "$npm_ver < $REQ_NPM"; }
  elif ! $SKIP_FRONTEND; then
    report FAIL "npm >= $REQ_NPM" "not installed (bundled with Node)"
  fi

  # --- Docker / compose (optional; blocks specific flags only) ---
  if docker_available; then
    local dc_ver; dc_ver="$(docker compose version --short 2>/dev/null || echo unknown)"
    report OK "docker + compose plugin" "daemon reachable (compose v$dc_ver)"
  else
    report WARN "docker" "daemon unavailable — [--with-infra] will be refused"
  fi

  # --- Pinned manifests present (install targets must exist before pulling) ---
  local f
  for f in \
    "ERP-BACKEND/requirements.txt" \
    "ERP-BACKEND/dev-requirements.txt" \
    "frontend/package.json" \
    "frontend/package-lock.json" \
    "$REQ_COMPOSE_FILE" ; do
    if [[ -f "$ROOT_DIR/$f" ]]; then
      report OK "manifest $f" "present"
    elif [[ "$f" == "$REQ_COMPOSE_FILE" ]]; then
      report WARN "manifest $f" "missing — compose workflows disabled"
    else
      report FAIL "manifest $f" "missing — cannot install pinned deps"
    fi
  done

  # --- Repo writability (venv/.env generation targets) ---
  if [[ -w "$ROOT_DIR" ]]; then
    report OK "workspace writable" "$ROOT_DIR"
  else
    report FAIL "workspace writable" "$ROOT_DIR is not writable"
  fi

  # --- GitHub CLI (only required when secrets sync is triggered) ---
  if $SYNC_SECRETS; then
    if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
      report OK "gh CLI (authenticated)" "$(gh --version | head -1)"
    else
      report FAIL "gh CLI authenticated" "required because --sync-secrets was requested"
    fi
  fi

  printf '\n==> Preflight summary: %d error(s), %d warning(s)\n' "$errors" "$warnings"
  if (( errors > 0 )); then
    die "pre-configuration check failed — fix the ✘ items above (or run with --skip-preflight to override at your own risk)"
  fi
  (( warnings > 0 )) && warn "preflight passed with $warnings warning(s); optional features may be disabled"
  log "✅ Pre-configuration check passed — proceeding to installs"
}

# ---------------------------------------------------------------------------
# Version-comparison helpers used by both preflight and toolchain checks.
# ---------------------------------------------------------------------------
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

# Centralized secret/variable registry — single source of truth for all env files.
# Two scopes, deliberately kept separate:
#   backend  — keys written into ERP-BACKEND/.env. Fields MUST match the
#              Settings model in ERP-BACKEND/app/core/config.py (extra="forbid":
#              any unknown key here makes the backend refuse to start).
#   compose  — keys written ONLY to .env.compose for docker-compose
#              interpolation (see .env.compose.example header warning).
# Format: "description|generator|required_for"
declare -A SECRET_SPECS=(
  # --- Backend settings (Settings model) ---
  ["SECRET_KEY"]="Application secret key|token_urlsafe(48)|all"
  ["POSTGRES_PASSWORD"]="PostgreSQL password|token_hex(24)|production,staging,compose"
  ["REDIS_PASSWORD"]="Redis password|token_hex(24)|staging,production,compose"
  ["DB_HOST"]="Production DB host|from_github|production"
  ["DB_PASSWORD"]="Production DB password|from_github|production"
  ["DOCKERHUB_TOKEN"]="Docker Hub PAT|from_github|ci,production"
  # --- Compose-only variables (never placed in the backend .env) ---
  ["REDIS_USER"]="Redis username (compose only; unused by app config)|default:default|compose"
  ["REDIS_ACCOUNT_NUMBER"]="Upstash Redis account (external REST rate limiting; compose only)|from_github|production"
  ["API_REDIS_KEY"]="Upstash Redis REST API key (compose only)|from_github|production"
  ["OLLAMA_IMAGE_TAG"]="Ollama image tag (k8s/compose manifest pinning; compose only)|fixed:0.5.4|all"
)

# Generate secure values using system python3 (no venv dependency)
generate_secure_value() {
  local spec="$1"
  case "$spec" in
    token_urlsafe* ) local n="${spec#token_urlsafe(}"; n="${n%)}"; python3 -c "import secrets; print(secrets.token_urlsafe($n))" ;;
    token_hex* ) local n="${spec#token_hex(}"; n="${n%)}"; python3 -c "import secrets; print(secrets.token_hex($n))" ;;
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
  log "Syncing GitHub secrets metadata..."
  check_gh_auth
  local owner_repo gh_secrets
  owner_repo="$(gh_owner_repo)"
  gh_secrets="$(gh secret list --repo "$owner_repo" --json name 2>/dev/null || echo '[]')"
  log "Available GitHub secrets: $(echo "$gh_secrets" | python3 -c "import sys, json; [print(x['name'], end=' ') for x in json.load(sys.stdin)]" 2>/dev/null || echo "jq not available")"
  log "Note: Secret values are not readable via GitHub API — they must be set in CI/CD environment"
}

auto_configure_all() {
  log "🔧 Auto-configuring environment ($ENV_TYPE)..."

  # 1. Ensure venv exists for later use (but generate secrets with system python)
  if [[ ! -d "$VENV_DIR" ]]; then
    local py; py="$(python_cmd)"
    "$py" -m venv "$VENV_DIR"
  fi
  "$VENV_DIR/bin/pip" install --quiet --upgrade pip
  "$VENV_DIR/bin/pip" install --quiet -r "$BACKEND_DIR/requirements.txt"
  "$VENV_DIR/bin/pip" install --quiet -r "$BACKEND_DIR/dev-requirements.txt"

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

  # 4. Generate backend .env — ONLY fields defined in Settings model (extra="forbid")
  local backend_env="$BACKEND_DIR/.env"
  if [[ -f "$backend_env" && "$FORCE" != "true" ]]; then
    log "Keeping existing $backend_env (use --force to regenerate)"
  else
    log "Generating $backend_env..."
    mkdir -p "$BACKEND_DIR/.local"

    # Per-tier values (all keys exist in app/core/config.py Settings).
    local db_url db_path log_level debug origins typesafe jwt_min
    local tok_min ref_days bcrypt_rounds idem_ttl rl_requests otel otel_endpoint redis_url
    redis_url=""
    case "$ENV_TYPE" in
      development)
        db_url="sqlite+aiosqlite:///$BACKEND_DIR/.local/erp03.sqlite3"
        db_path="$BACKEND_DIR/.local/erp03.sqlite3"
        log_level="DEBUG"; debug="true"
        origins="http://localhost:3000,http://localhost:5173,http://localhost:8000"
        typesafe="false"; jwt_min="30"
        tok_min="30"; ref_days="7"; bcrypt_rounds="12"; idem_ttl="24"
        rl_requests="100"; otel="false"; otel_endpoint=""
        ;;
      staging|production)
        local db_host="${SECRETS[DB_HOST]:-postgres}"
        local db_pass="${SECRETS[DB_PASSWORD]}"
        if [[ -z "$db_pass" || "$db_pass" == "__GITHUB_SECRET__" ]]; then
          warn "DB_PASSWORD not set locally; generating an ephemeral strong password"
          db_pass="$(generate_secure_value 'token_hex(24)')"
        fi
        db_url="postgresql+asyncpg://erp03:${db_pass}@${db_host}:5432/erp03"
        # legacy SQLite-backed transaction store path (see app/api/transactions.py)
        db_path="/app/.local/erp03.sqlite3"
        log_level="INFO"; debug="false"
        typesafe="true"; jwt_min="15"
        tok_min="15"; ref_days="30"; bcrypt_rounds="14"; idem_ttl="168"
        rl_requests="1000"; otel="true"; otel_endpoint="http://otel-collector:4317"
        redis_url="redis://:${SECRETS[REDIS_PASSWORD]}@redis:6379/0"
        if [[ "$ENV_TYPE" == "staging" ]]; then
          origins="${STAGING_CORS_ORIGINS:-https://staging.your-domain.com}"
        else
          origins="${PRODUCTION_CORS_ORIGINS:-https://your-domain.com}"
        fi
        ;;
    esac

    cat > "$backend_env" <<EOF
# ERP03 Backend Config — AUTO-GENERATED $ENV_TYPE by scripts/setup.sh
# Every key below MUST exist in ERP-BACKEND/app/core/config.py Settings (extra="forbid").
ENVIRONMENT=$ENV_TYPE
SECRET_KEY=${SECRETS[SECRET_KEY]}
LOG_LEVEL=$log_level
DATABASE_URL=$db_url
DATABASE_PATH=$db_path
DB_POOL_SIZE=$POOL_SIZE
DB_MAX_OVERFLOW=$POOL_OVERFLOW
DB_POOL_RECYCLE=$POOL_RECYCLE
DB_ECHO=false
CORS_ORIGINS=$origins
TYPESAFE_ENABLED=$typesafe
TYPESAFE_API_KEY=
JWT_EXPIRY_MINUTES=$jwt_min
REDIS_URL=$redis_url
REDIS_PASSWORD=${SECRETS[REDIS_PASSWORD]}
REDIS_DB=0
API_V1_PREFIX=/api/v1
API_TITLE=ERP03 API
API_VERSION=1.1.0
API_DOCS_URL=/docs
API_REDOC_URL=/redoc
ACCESS_TOKEN_EXPIRE_MINUTES=$tok_min
REFRESH_TOKEN_EXPIRE_DAYS=$ref_days
PASSWORD_MIN_LENGTH=12
BCRYPT_ROUNDS=$bcrypt_rounds
IDEMPOTENCY_TTL_HOURS=$idem_ttl
IDEMPOTENCY_CLEANUP_INTERVAL=3600
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=$rl_requests
RATE_LIMIT_WINDOW=60
TRUSTED_PROXIES=
WEBHOOK_SECRET=
WEBHOOK_TIMEOUT=30
OTEL_ENABLED=$otel
OTEL_EXPORTER_OTLP_ENDPOINT=$otel_endpoint
DEBUG=$debug
EOF
    chmod 600 "$backend_env"
    log "  ✓ Backend config written"
  fi

  # 5. Generate .env.compose for Docker Compose (both prod and dev)
  local compose_env="$ROOT_DIR/.env.compose"
  if [[ -f "$compose_env" && "$FORCE" != "true" ]]; then
    log "Keeping existing $compose_env (use --force to regenerate)"
  else
    log "Generating $compose_env..."
    # Use same passwords across all configs for consistency
    local pg_pass="${SECRETS[POSTGRES_PASSWORD]}"
    local redis_pass="${SECRETS[REDIS_PASSWORD]}"
    local redis_user="${SECRETS[REDIS_USER]}"
    cat > "$compose_env" <<EOF
# ERP03 Docker Compose Environment — AUTO-GENERATED
# Environment: ${ENV_TYPE}
# Usage: docker compose --env-file .env.compose up -d
#        docker compose -f docker-compose.dev.yml --env-file .env.compose up -d

# Database (use 'erp03' consistently everywhere)
POSTGRES_DB=erp03
POSTGRES_USER=erp03
POSTGRES_PASSWORD=${pg_pass}
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_PASSWORD=${redis_pass}
REDIS_USER=${redis_user}
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://:${redis_pass}@redis:6379/0
REDIS_ACCOUNT_NUMBER=${SECRETS[REDIS_ACCOUNT_NUMBER]}
API_REDIS_KEY=${SECRETS[API_REDIS_KEY]}

# Docker Hub (for container.yml CI)
DOCKERHUB_USERNAME=${DOCKERHUB_USERNAME:-powerrangeranikg}
DOCKERHUB_TOKEN=${SECRETS[DOCKERHUB_TOKEN]}
DOCKERHUB_IMAGE_BACKEND=powerrangeranikg/erp03-backend
DOCKERHUB_IMAGE_FRONTEND=powerrangeranikg/erp03-frontend
IMAGE_TAG=${IMAGE_TAG:-latest}

# Backend (production uses pre-built images; dev uses this for build-time)
SECRET_KEY=${SECRETS[SECRET_KEY]}
ENVIRONMENT=${ENV_TYPE}
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
API_URL=http://localhost:8000
WS_URL=ws://localhost:8000
DATABASE_URL=postgresql+asyncpg://erp03:${pg_pass}@postgres:5432/erp03
OLLAMA_URL=http://ollama:11434

# Frontend (Vite build-time injection)
VITE_API_BASE_URL=/api
VITE_WS_URL=ws://localhost:8000
VITE_APP_TITLE=ERP03

# Ollama
OLLAMA_IMAGE_TAG=${SECRETS[OLLAMA_IMAGE_TAG]}

# NGINX (production reverse proxy)
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem
EOF
    chmod 600 "$compose_env"
    log "  ✓ Compose config written"
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

  # 7. Generate .env.example for documentation (no secrets, just templates)
  local example_env="$ROOT_DIR/.env.example"
  if [[ ! -f "$example_env" || "$FORCE" == "true" ]]; then
    log "Generating $example_env..."
    cat > "$example_env" <<'EOF'
# ERP03 Environment Template — Copy to .env and fill in values
# NEVER commit real credentials to version control

# Core
ENVIRONMENT=development
SECRET_KEY=your-secret-key-min-32-chars
LOG_LEVEL=DEBUG

# Database (SQLite for dev, PostgreSQL for production)
DATABASE_URL=sqlite+aiosqlite:///./.local/erp03.sqlite3
DATABASE_PATH=./.local/erp03.sqlite3

# Database Pool (auto-tuned by ENVIRONMENT)
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=1800
DB_ECHO=false

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
REDIS_DB=0

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# TypeSafe (optional)
TYPESAFE_ENABLED=false
TYPESAFE_API_KEY=

# JWT
JWT_EXPIRY_MINUTES=30

# Auth
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_MIN_LENGTH=12
BCRYPT_ROUNDS=12

# Idempotency
IDEMPOTENCY_TTL_HOURS=24
IDEMPOTENCY_CLEANUP_INTERVAL=3600

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Webhooks
WEBHOOK_SECRET=
WEBHOOK_TIMEOUT=30

# Observability
OTEL_ENABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=

# Debug
DEBUG=true
EOF
    log "  ✓ Example config written"
  fi

  # 8. Verify configuration loads correctly — hard gate: Settings uses
  # extra="forbid", so any drift between this generated file and the model
  # must fail setup loudly instead of failing silently at first request.
  # The check forces a hermetic SQLite URL (never connects to real Postgres)
  # and keeps ENVIRONMENT from the .env so production validators still run.
  log "Verifying configuration..."
  if ! ( cd "$BACKEND_DIR" && DATABASE_URL="sqlite+aiosqlite:////tmp/erp03-setup-check.sqlite3" \
      "$VENV_DIR/bin/python" -c '
from app.core.config import Settings
s = Settings()
print(f"  \u2713 Settings loaded ({s.environment}): pool={s.db_pool_size}/{s.db_max_overflow} "
      f"origins={len(s.cors_origin_list)} redis={\"on\" if s.redis_url else \"off\"}")
' ); then
    die "Generated $backend_env does not match the Settings model (extra=\"forbid\"). Fix the env block or re-run with --force."
  fi

  log "✅ Auto-configuration complete!"
  log ""
  log "📋 Generated files:"
  log "  • $backend_env"
  log "  • $compose_env"
  log "  • $frontend_env"
  log "  • $example_env"
  log ""
  log "🚀 Ready to start:"
  log "  source .venv/bin/activate"
  log "  ./scripts/setup.sh --with-infra   # Start all services (uses .env.compose)"
  log "  ./scripts/setup.sh --qualify      # Run full test gate"
}

# ---------------------------------------------------------------------------
# 4. Backend environment provisioning (legacy path — kept for compatibility)
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
# 5. Frontend dependencies
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
# 6. Optional infrastructure + smoke verification
# ---------------------------------------------------------------------------
start_infra() {
  if ! docker_available; then
    die "--with-infra requested but Docker daemon is unavailable"
  fi
  log "Starting Docker Compose stack using .env.compose..."
  # Use the generated .env.compose for consistent secrets
  (cd "$ROOT_DIR" && compose_cmd --env-file .env.compose up -d --build)
  log "Compose stack started: API http://localhost:8000/docs · UI http://localhost:3000"
}

smoke_test() {
  log "Running hermetic test suite as bootstrap smoke test"
  # Force hermetic SQLite for smoke test regardless of .env config
  # Must override ENVIRONMENT too, otherwise production validation fails
  local tmpdir="$(mktemp -d)"
  local db_url="sqlite+aiosqlite:///$tmpdir/erp03.sqlite3"
  local db_path="$tmpdir/erp03.sqlite3"
  (cd "$BACKEND_DIR" && ENVIRONMENT=development DATABASE_URL="$db_url" DATABASE_PATH="$db_path" "$VENV_DIR/bin/pytest" -q)
}

# ---------------------------------------------------------------------------
main() {
  detect_platform
  arch_lower="$(echo "$ARCH" | tr '[:upper:]' '[:lower:]')"

  # Pre-configuration gate: runs FIRST, before any install trigger (venv
  # creation, pip pulls, npm ci) or secrets sync, so incompatible hosts fail
  # fast with an accurate report instead of a half-provisioned environment.
  if $WITH_PREFLIGHT; then
    preflight_check
  else
    warn "pre-configuration check skipped (--skip-preflight)"
  fi
  if $PREFLIGHT_ONLY; then
    log "Preflight-only run requested (--preflight-only); no installs performed."
    exit 0
  fi

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