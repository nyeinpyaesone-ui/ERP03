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

log()  { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
  sed -n '3,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-infra) WITH_INFRA=true ;;
    --qualify) QUALIFY=true ;;
    --skip-frontend) SKIP_FRONTEND=true ;;
    --help|-h) usage; exit 0 ;;
    *) die "unknown option: $1 (see --help)" ;;
  esac
  shift
done

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
# 3. Backend environment provisioning
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
  pip install --quiet --upgrade pip
  pip install --quiet --requirement "$BACKEND_DIR/requirements.txt"
  pip install --quiet ruff==0.17.1
  log "Backend dependencies installed (pinned versions verified by CI)"
}

# ---------------------------------------------------------------------------
# 4. Secure local configuration (.env)
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
DATABASE_URL=postgresql+asyncpg://erp03:erp03@127.0.0.1:5432/erp03
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
DATABASE_PATH=./.local/erp03.sqlite3
EOF
  mkdir -p "$BACKEND_DIR/.local"
  chmod 600 "$env_file"
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
  (cd "$FRONTEND_DIR" && npm install --no-audit --no-fund --silent)
}

# ---------------------------------------------------------------------------
# 6. Optional infrastructure + smoke verification
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
