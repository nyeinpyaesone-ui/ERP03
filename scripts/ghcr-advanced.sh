#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

# ERP03 — Advanced GHCR Image Service
# Auto-detect repository/images, build, push and verify.
# Credentials are NEVER stored in this script.

REGISTRY="${REGISTRY:-ghcr.io}"
COMPOSE="${COMPOSE:-docker-compose.prod.yml}"
MODE="${MODE:-push}" # check | build | push
TAG="${IMAGE_TAG:-}"
PLATFORM="${PLATFORM:-linux/amd64}"
PUSH_LATEST="${PUSH_LATEST:-false}"

need() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: missing command: $1" >&2; exit 1; }; }
die() { echo "ERROR: $*" >&2; exit 1; }

need docker
need git
need awk
need sed

docker info >/dev/null 2>&1 || die "Docker daemon unavailable"

OWNER="nyeinpyaesone-ui"
REPO="ERP03"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  REMOTE="$(git remote get-url origin 2>/dev/null || true)"
  if [[ "$REMOTE" =~ github\.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
  fi
  COMMIT="$(git rev-parse HEAD)"
else
  COMMIT="unknown"
fi

IMAGE_REPO="${REGISTRY}/${OWNER,,}/${REPO,,}"
BACKEND="${IMAGE_REPO}-backend"
FRONTEND="${IMAGE_REPO}-frontend"
TAG="${TAG:-$COMMIT}"
[[ "$TAG" =~ ^[A-Za-z0-9._-]+$ ]] || die "Invalid image tag: $TAG"

# Confirm production compose remains valid before publishing.
[[ -f "$COMPOSE" ]] || die "$COMPOSE not found"
docker compose -f "$COMPOSE" config >/dev/null

# Detect Docker build contexts from repository conventions.
BACKEND_CONTEXT="${BACKEND_CONTEXT:-}"
FRONTEND_CONTEXT="${FRONTEND_CONTEXT:-}"
[[ -n "$BACKEND_CONTEXT" ]] || [[ ! -d ERP-BACKEND ]] || BACKEND_CONTEXT=ERP-BACKEND
[[ -n "$FRONTEND_CONTEXT" ]] || [[ ! -d ERP-FRONTEND ]] || FRONTEND_CONTEXT=ERP-FRONTEND

check_image() {
  local image="$1"
  echo "Checking ${image}:${TAG}"
  docker manifest inspect "${image}:${TAG}" >/dev/null 2>&1
}

build_image() {
  local image="$1" context="$2"
  [[ -n "$context" && -d "$context" ]] || die "Build context not found for $image: ${context:-unset}"
  docker build --pull --platform "$PLATFORM" -t "${image}:${TAG}" "$context"
}

push_image() {
  local image="$1"
  docker push "${image}:${TAG}"
  docker inspect --format='{{index .RepoDigests 0}}' "${image}:${TAG}" 2>/dev/null || true
}

echo "ERP03 GHCR"
echo "Registry : $REGISTRY"
echo "Owner    : $OWNER"
echo "Backend  : ${BACKEND}:${TAG}"
echo "Frontend : ${FRONTEND}:${TAG}"
echo "Commit   : $COMMIT"

case "$MODE" in
  check)
    check_image "$BACKEND" && echo "backend: PRESENT" || echo "backend: NOT FOUND"
    check_image "$FRONTEND" && echo "frontend: PRESENT" || echo "frontend: NOT FOUND"
    exit 0
    ;;
  build)
    build_image "$BACKEND" "$BACKEND_CONTEXT"
    build_image "$FRONTEND" "$FRONTEND_CONTEXT"
    ;;
  push)
    # Authentication must already exist in Docker's credential store.
    docker system info >/dev/null
    build_image "$BACKEND" "$BACKEND_CONTEXT"
    build_image "$FRONTEND" "$FRONTEND_CONTEXT"
    push_image "$BACKEND"
    push_image "$FRONTEND"
    ;;
  *) die "MODE must be check, build, or push" ;;
esac

if [[ "$MODE" == "push" && "$PUSH_LATEST" == "true" ]]; then
  docker tag "${BACKEND}:${TAG}" "${BACKEND}:latest"
  docker tag "${FRONTEND}:${TAG}" "${FRONTEND}:latest"
  docker push "${BACKEND}:latest"
  docker push "${FRONTEND}:latest"
fi

if [[ "$MODE" == "push" ]]; then
  check_image "$BACKEND" || die "Backend verification failed"
  check_image "$FRONTEND" || die "Frontend verification failed"
fi

echo "GHCR operation completed successfully."
