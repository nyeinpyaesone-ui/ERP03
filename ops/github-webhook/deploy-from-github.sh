#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/erp03}"
BRANCH="${GITHUB_BRANCH:-main}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
LOCK_FILE="${APP_DIR}/.deploy.lock"

exec 9>"$LOCK_FILE"
flock -n 9 || exit 0

cd "$APP_DIR"
git fetch --prune origin "$BRANCH"
git checkout -B "$BRANCH" "origin/$BRANCH"
git reset --hard "origin/$BRANCH"

docker compose -f "$COMPOSE_FILE" pull erp-backend frontend
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

for i in {1..30}; do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null; then
    exit 0
  fi
  sleep 2
done

exit 1
