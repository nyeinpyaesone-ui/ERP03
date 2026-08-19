#!/usr/bin/env bash
###############################################################################
# ERP03 — Development Environment Setup
# Host/devcontainer bootstrap for the active ERP03 architecture.
###############################################################################
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

info() { printf '[i] %s\n' "$1"; }
ok()   { printf '[✓] %s\n' "$1"; }
fail() { printf '[✗] %s\n' "$1" >&2; exit 1; }

command -v git >/dev/null || fail "git is required"
command -v python3 >/dev/null || fail "python3 is required"
command -v pip3 >/dev/null || fail "pip3 is required"
command -v node >/dev/null || fail "Node.js is required"
command -v npm >/dev/null || fail "npm is required"
command -v docker >/dev/null || fail "Docker is required"

docker compose version >/dev/null 2>&1 || fail "Docker Compose plugin is required"

docker info >/dev/null 2>&1 || fail "Docker daemon is not available"

PYTHON_MAJOR_MINOR="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
[ "$PYTHON_MAJOR_MINOR" = "3.11" ] || fail "ERP03 backend targets Python 3.11; found $PYTHON_MAJOR_MINOR"

NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
[ "$NODE_MAJOR" -ge 20 ] || fail "ERP03 frontend requires Node.js 20+; found $NODE_MAJOR"

ok "Host/runtime prerequisites validated"

# Root development configuration is the authoritative Compose configuration.
if [ ! -f .env ]; then
  [ -f .env.example ] || fail "Missing .env.example"
  cp .env.example .env
  ok "Created root .env from .env.example"
fi

# Replace development placeholders only; never overwrite an existing real value.
python3 - <<'PY'
from pathlib import Path
import secrets

p = Path('.env')
s = p.read_text()
password = secrets.token_urlsafe(24)
secret = secrets.token_urlsafe(48)
s = s.replace('replace-with-random-development-secret', password)
s = s.replace('replace-with-at-least-32-random-characters', secret)
p.write_text(s)
PY

# ERP-BACKEND supports direct local Python development in addition to Compose.
if [ -f ERP-BACKEND/requirements.txt ]; then
  if [ ! -d ERP-BACKEND/.venv ]; then
    python3 -m venv ERP-BACKEND/.venv
    ok "Created ERP-BACKEND/.venv"
  fi
  ERP-BACKEND/.venv/bin/python -m pip install --upgrade pip
  ERP-BACKEND/.venv/bin/pip install -r ERP-BACKEND/requirements.txt
  ok "ERP-BACKEND Python dependencies installed"
fi

# The maintained web client is ERP-BACKEND/frontend-react, not the legacy frontend/ path.
if [ -f ERP-BACKEND/frontend-react/package.json ]; then
  cd ERP-BACKEND/frontend-react
  npm install
  cd "$ROOT_DIR"
  ok "ERP frontend dependencies installed"
fi

# Validate the repository's real development runtime definition without starting it.
docker compose config >/dev/null
ok "docker-compose.yml validated"

if [ "${START_SERVICES:-0}" = "1" ]; then
  docker compose up -d
  ok "ERP03 development services started"
else
  info "Services not started. Run: START_SERVICES=1 ./scripts/setup.sh"
fi

echo
echo "ERP03 development environment is ready."
echo "  API:      http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  Ollama:   http://localhost:11434"
