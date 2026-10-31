#!/usr/bin/env bash
set -Eeuo pipefail

AGENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env.sh
source "$AGENT_DIR/env.sh"
agent_detect
cd "$AGENT_ROOT_DIR"

mkdir -p .agent/evidence
agent_record_env .agent/evidence

if [ "$AGENT_TERMUX" -eq 1 ]; then
  cat >&2 <<'MSG'
ERROR: native Termux detected (bionic libc).
manylinux aarch64 wheels (asyncpg, cryptography, argon2-cffi) cannot install here.

Enter the glibc environment first:

  pkg install proot-distro
  proot-distro install ubuntu
  proot-distro login ubuntu --user builder --shared-tmp

Then re-run:  bash scripts/agent/bootstrap.sh
MSG
  exit 3
fi

if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: node not found (need >= 20.19; CI uses 22)" >&2
  exit 4
fi

NODE_MAJOR="$(node -v | sed 's/^v\([0-9]*\).*/\1/')"
if [ "$NODE_MAJOR" -lt 20 ]; then
  echo "ERROR: node $(node -v) too old (Vite 7 needs >= 20.19)" >&2
  exit 4
fi
[ "$NODE_MAJOR" -eq 22 ] || echo "warn: CI uses Node 22, found $(node -v)" >&2

# Toolchain, venv, pinned backend deps, .env generation. Idempotent.
bash scripts/setup.sh --skip-frontend --env-type development

if [ ! -d frontend/node_modules ]; then
  ( cd frontend && npm ci --no-audit --no-fund --include=optional )
fi

if [ "$AGENT_ARCH" = "aarch64" ] \
   && [ ! -d frontend/node_modules/@rollup/rollup-linux-arm64-gnu ]; then
  echo "warn: arm64 rollup binary missing; reinstalling node_modules" >&2
  ( cd frontend && rm -rf node_modules && npm ci --no-audit --no-fund --include=optional )
fi

if [ "${AGENT_SERVICES:-0}" = "1" ]; then
  if command -v redis-server >/dev/null 2>&1; then
    redis-cli ping >/dev/null 2>&1 || redis-server --daemonize yes --port 6379
  fi
  if [ "$AGENT_IS_ROOT" -eq 1 ]; then
    echo "skip: local postgres (refuses to run as root; use --user or SQLite)" >&2
  fi
fi

if [ "$AGENT_PROOT" -eq 1 ] || [ "$AGENT_ARCH" = "aarch64" ]; then
  export CHOKIDAR_USEPOLLING=1
  export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=512}"
fi

echo "bootstrap: env=$AGENT_ENV_NAME arch=$AGENT_ARCH docker=$AGENT_DOCKER node=$(node -v)"
