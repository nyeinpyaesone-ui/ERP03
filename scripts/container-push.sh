#!/usr/bin/env bash
# Build, scan and push the backend and frontend images from the current tree.
#
# Usage:
#   scripts/container-push.sh                # registry from .env.container (default ghcr)
#   CONTAINER_REGISTRY=dockerhub scripts/container-push.sh
#   CONTAINER_ALLOW_DIRTY=1 ...              # required when the tree has uncommitted changes
#   SKIP_SCAN=1 ...                          # skip trivy (trivy must be installed otherwise)
#
# Local equivalent of the `Container Push` workflow. Tags: <sha> and <branch>.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if [ "${CONTAINER_PRINT_ONLY:-0}" = "1" ]; then
  set -euo pipefail
else
  set -Eeuo pipefail
fi

# --- profile -----------------------------------------------------------------
[ -f .env.container ] && . ./.env.container
registry="${CONTAINER_REGISTRY:-ghcr}"
case "${registry}" in ghcr|dockerhub) ;; *) echo "ERROR: CONTAINER_REGISTRY must be ghcr or dockerhub" >&2; exit 1 ;; esac

# --- image coordinates --------------------------------------------------------
remote="$(git remote get-url origin 2>/dev/null | sed 's#.*github\.com[:/]##; s#\.git$##')" || true
[ -n "${remote}" ] || { echo "ERROR: no 'origin' git remote; set IMAGE_BASE manually" >&2; exit 1; }
default_base() {
  case "${registry}" in
    ghcr) echo "ghcr.io/$(printf '%s' "${remote}" | tr '[:upper:]' '[:lower:]')" ;;
    dockerhub)
      [ -n "${DOCKERHUB_USERNAME:-${DOCKERHUB_USERNAME_FILE:-}}" ] || { echo "ERROR: set DOCKERHUB_USERNAME in .env.container (run scripts/env-setup.sh)" >&2; exit 1; }
      echo "docker.io/$(printf '%s' "${DOCKERHUB_USERNAME}" | tr '[:upper:]' '[:lower:]')/$(printf '%s' "${remote##*/}" | tr '[:upper:]' '[:lower:]')"
      ;;
  esac
}
image_base="${IMAGE_BASE:-$(default_base)}"
sha="$(git rev-parse HEAD)"
branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
[ -n "${branch}" ] && [ "${branch}" != "HEAD" ] || branch="detached-${sha#"${sha%"${sha#???????}"}"}"
branch_tag="$(printf '%s' "${branch}" | tr '[:upper:]' '[:lower:]' | tr '/' '-')"

echo "Registry  : ${registry}"
echo "Base      : ${image_base}"
echo "Tags      : ${sha:0:7} + ${branch_tag}"

if [ "${CONTAINER_PRINT_ONLY:-0}" = "1" ]; then
  echo "backend  : ${image_base}-backend:${sha}"
  echo "frontend : ${image_base}-frontend:${sha}"
  exit 0
fi

# --- preflight ----------------------------------------------------------------
dirty="$(git status --porcelain)"
if [ -n "${dirty}" ] && [ "${CONTAINER_ALLOW_DIRTY:-0}" != "1" ]; then
  echo "ERROR: uncommitted changes; the image would not match ${sha}. Commit, stash, or set CONTAINER_ALLOW_DIRTY=1" >&2
  exit 1
fi

command -v docker >/dev/null 2>&1 || { echo "ERROR: docker is not installed" >&2; exit 1; }

if [ "${registry}" = "dockerhub" ] && [ -n "${DOCKERHUB_USERNAME:-}" ] && [ -n "${DOCKERHUB_TOKEN:-}" ]; then
  printf '%s' "${DOCKERHUB_TOKEN}" | docker login docker.io --username "${DOCKERHUB_USERNAME}" --password-stdin
elif [ "${registry}" = "ghcr" ] && [ -n "${GHCR_TOKEN:-}" ]; then
  printf '%s' "${GHCR_TOKEN}" | docker login ghcr.io --username "${DOCKERHUB_USERNAME:-${ghcr_user:-$(printf '%s' "${remote%%/*}")}}" --password-stdin
else
  echo "NOTE: no stored token; assuming an existing '${registry}' docker login."
fi

if [ "${SKIP_SCAN:-0}" != "1" ]; then
  command -v trivy >/dev/null 2>&1 || { echo "ERROR: trivy not found (install it), or set SKIP_SCAN=1" >&2; exit 1; }
fi

# --- build, scan, push ---------------------------------------------------------
push_component() {
  component="$1"; context="$2"; dockerfile="$3"
  image="${image_base}-${component}"
  echo "== ${component}: building ${image}:${sha:0:7}"
  docker build --file "${dockerfile}" --tag "${image}:${sha}" "${context}"
  if [ "${SKIP_SCAN:-0}" != "1" ]; then
    echo "== ${component}: scanning"
    trivy image --severity CRITICAL,HIGH --ignore-unfixed --exit-code 1 --scanners vuln "${image}:${sha}"
  fi
  echo "== ${component}: pushing"
  docker tag "${image}:${sha}" "${image}:${branch_tag}"
  docker push "${image}:${sha}"
  docker push "${image}:${branch_tag}"
  echo "pushed: $(docker inspect --format '{{index .RepoDigests 0}}' "${image}:${sha}")"
}

push_component backend ERP-BACKEND ERP-BACKEND/Dockerfile
push_component frontend frontend frontend/Dockerfile

echo "Done."
