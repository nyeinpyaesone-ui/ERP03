#!/usr/bin/env bash
# scripts/agent/env.sh — environment detection. Sourced, never executed.
# Exports AGENT_* and provides agent_detect / agent_record_env.

agent_detect() {
  AGENT_OS="$(uname -s)"
  AGENT_ARCH="$(uname -m)"
  AGENT_KERNEL="$(uname -r)"
  AGENT_ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

  AGENT_TERMUX=0
  case "${PREFIX:-}" in
    *com.termux*) AGENT_TERMUX=1 ;;
  esac

  # proot Ubuntu runs on the Android kernel and has no PID namespace.
  # Kernel strings vary (`-android`, `-gki`, `6.17.0-PRoot-Distro`) — compare lowercased.
  AGENT_PROOT=0
  if [ "$AGENT_TERMUX" -eq 0 ]; then
    local _kernel_lc
    _kernel_lc="$(printf '%s' "$AGENT_KERNEL" | tr '[:upper:]' '[:lower:]')"
    case "$_kernel_lc" in
      *android*|*gki*|*proot*) AGENT_PROOT=1 ;;
    esac
  fi

  AGENT_CODESPACES=0
  if [ -n "${CODESPACES:-}" ]; then
    AGENT_CODESPACES=1
  fi

  AGENT_CI=0
  if [ "$AGENT_CODESPACES" -eq 0 ]; then
    if [ -f /.dockerenv ] || grep -qaE 'docker|containerd' /proc/1/cgroup 2>/dev/null; then
      AGENT_CI=1
    fi
  fi

  AGENT_DOCKER=0
  if command -v docker >/dev/null 2>&1; then
    if timeout 5 docker info >/dev/null 2>&1; then
      AGENT_DOCKER=1
    fi
  fi

  AGENT_IS_ROOT=0
  if [ "$(id -u)" -eq 0 ]; then AGENT_IS_ROOT=1; fi

  AGENT_HAS_SUDO=0
  if command -v sudo >/dev/null 2>&1; then AGENT_HAS_SUDO=1; fi

  # Explicit override always wins; heuristics are best-effort.
  case "${AGENT_ENV:-}" in
    termux)    AGENT_TERMUX=1; AGENT_PROOT=0; AGENT_CODESPACES=0; AGENT_CI=0 ;;
    proot)     AGENT_PROOT=1; AGENT_TERMUX=0; AGENT_CODESPACES=0; AGENT_CI=0 ;;
    codespace) AGENT_CODESPACES=1; AGENT_TERMUX=0; AGENT_PROOT=0; AGENT_CI=0 ;;
    ci)        AGENT_CI=1; AGENT_TERMUX=0; AGENT_PROOT=0; AGENT_CODESPACES=0 ;;
    local)     AGENT_TERMUX=0; AGENT_PROOT=0; AGENT_CODESPACES=0; AGENT_CI=0 ;;
  esac

  if   [ "$AGENT_TERMUX" -eq 1 ];     then AGENT_ENV_NAME=termux
  elif [ "$AGENT_PROOT" -eq 1 ];      then AGENT_ENV_NAME=proot
  elif [ "$AGENT_CODESPACES" -eq 1 ]; then AGENT_ENV_NAME=codespace
  elif [ "$AGENT_CI" -eq 1 ];         then AGENT_ENV_NAME=ci
  else AGENT_ENV_NAME=local
  fi

  export AGENT_OS AGENT_ARCH AGENT_KERNEL AGENT_ROOT_DIR AGENT_ENV_NAME \
         AGENT_TERMUX AGENT_PROOT AGENT_CODESPACES AGENT_CI AGENT_DOCKER \
         AGENT_IS_ROOT AGENT_HAS_SUDO
}

# agent_record_env <dir> — write <dir>/env.json (versions and booleans only).
agent_record_env() {
  local out="${1:?usage: agent_record_env <dir>}"
  local py="" node="" commit="none"
  mkdir -p "$out"
  command -v python3 >/dev/null 2>&1 && py="$(python3 -V 2>&1)"
  command -v node >/dev/null 2>&1 && node="$(node -v 2>&1)"
  commit="$(git -C "$AGENT_ROOT_DIR" rev-parse --short HEAD 2>/dev/null || echo none)"
  cat > "$out/env.json" <<JSON
{
  "env": "${AGENT_ENV_NAME}",
  "os": "${AGENT_OS}",
  "arch": "${AGENT_ARCH}",
  "kernel": "${AGENT_KERNEL}",
  "termux": ${AGENT_TERMUX},
  "proot": ${AGENT_PROOT},
  "codespaces": ${AGENT_CODESPACES},
  "ci": ${AGENT_CI},
  "docker": ${AGENT_DOCKER},
  "root": ${AGENT_IS_ROOT},
  "python": "${py}",
  "node": "${node}",
  "commit": "${commit}"
}
JSON
}
