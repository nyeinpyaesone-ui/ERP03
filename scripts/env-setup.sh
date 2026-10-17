#!/usr/bin/env bash
# Set up container-registry credentials for `scripts/container-push.sh`.
#
# Usage:
#   scripts/env-setup.sh                          # interactive
#   scripts/env-setup.sh --registry ghcr          # GHCR; optional --ghcr-user/--ghcr-token
#   scripts/env-setup.sh --registry dockerhub --dockerhub-user NAME --dockerhub-token TOKEN
#
# Writes .env.container (chmod 600, gitignored). Existing files are overwritten.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT}/.env.container"

registry=""; ghcr_user=""; ghcr_token=""; hub_user=""; hub_token=""

while [ $# -gt 0 ]; do
  case "$1" in
    --registry) registry="$2"; shift 2 ;;
    --ghcr-user) ghcr_user="$2"; shift 2 ;;
    --ghcr-token) ghcr_token="$2"; shift 2 ;;
    --dockerhub-user) hub_user="$2"; shift 2 ;;
    --dockerhub-token) hub_token="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [ -z "${registry}" ]; then
  printf "Registry [ghcr|dockerhub] (ghcr): "
  read -r registry
  registry="${registry:-ghcr}"
fi
case "${registry}" in
  ghcr|dockerhub) ;;
  *) echo "ERROR: registry must be ghcr or dockerhub" >&2; exit 1 ;;
esac

if [ -z "${ghcr_user}" ] || [ -z "${hub_user}" ]; then
  if [ "${registry}" = "ghcr" ]; then
    printf "GitHub username [%s]: " "$(git -C "${ROOT}" config user.name 2>/dev/null || echo "")"
    read -r ghcr_user
    printf "GHCR token (PAT with write:packages; blank = reuse an existing `docker login`) : "
    read -r ghcr_token
  else
    printf "Docker Hub username: "
    read -r hub_user
    printf "Docker Hub token: "
    read -r hub_token
  fi
fi

image_base=""
case "${registry}" in
  ghcr)
    remote="$(git -C "${ROOT}" remote get-url origin 2>/dev/null | sed 's#.*github\.com[:/]##; s#\.git$##')" || remote=""
    ghcr_user="${ghcr_user:-$(printf '%s' "${remote}" | cut -d/ -f1)}"
    image_base="ghcr.io/$(printf '%s' "${remote}" | tr '[:upper:]' '[:lower:]')"
    ;;
  dockerhub)
    [ -n "${hub_user}" ] || { echo "ERROR: --dockerhub-user is required" >&2; exit 1; }
    repo="$(git -C "${ROOT}" remote get-url origin 2>/dev/null | sed 's#.*/##; s#\.git$##')"
    image_base="docker.io/$(printf '%s' "${hub_user}" | tr '[:upper:]' '[:lower:]')/$(printf '%s' "${repo}" | tr '[:upper:]' '[:lower:]')"
    ;;
esac

umask 077
{
  echo "CONTAINER_REGISTRY=${registry}"
  echo "IMAGE_BASE=${image_base}"
  [ "${registry}" = "ghcr" ] && [ -n "${ghcr_token}" ] && echo "GHCR_TOKEN=${ghcr_token}"
  [ "${registry}" = "dockerhub" ] && echo "DOCKERHUB_USERNAME=${hub_user}" && echo "DOCKERHUB_TOKEN=${hub_token}"
} > "${ENV_FILE}"
chmod 600 "${ENV_FILE}"

command -v docker >/dev/null 2>&1 || { echo "WARNING: docker is not installed; set it up before pushing."; }
if [ -n "${ghcr_token}" ]; then
  printf '%s' "${ghcr_token}" | docker login ghcr.io --username "${ghcr_user}" --password-stdin || echo "WARNING: GHCR login failed; run 'docker login ghcr.io' manually."
elif [ -n "${hub_token}" ]; then
  printf '%s' "${hub_token}" | docker login docker.io --username "${hub_user}" --password-stdin || echo "WARNING: Docker Hub login failed."
else
  echo "No token stored (env file keeps credentials out). Ensure '${registry}' login exists before pushing."
fi

echo "Profile written: ${ENV_FILE}"
echo "Next: make container-push"
