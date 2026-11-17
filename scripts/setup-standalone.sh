#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env.standalone"
COMPOSE_FILE="$ROOT_DIR/docker-compose.standalone.yml"
PROJECT_NAME="erp03-standalone"
HTTP_PORT="${ERP03_HTTP_PORT:-3000}"

log() { printf '\n==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

command -v docker >/dev/null 2>&1 || die "Docker is required."
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 plugin is required."
command -v python3 >/dev/null 2>&1 || die "python3 is required to generate a local signing key."
command -v curl >/dev/null 2>&1 || die "curl is required for the HTTP readiness checks."
[[ -f "$COMPOSE_FILE" ]] || die "Missing $COMPOSE_FILE."

if [[ ! -f "$ENV_FILE" ]]; then
  log "Generating a private, local-only environment file"
  secret="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
  umask 077
  tmp_file="$(mktemp "$ROOT_DIR/.env.standalone.XXXXXX")"
  {
    printf 'SECRET_KEY=%s\n' "$secret"
    printf 'ERP03_HTTP_PORT=%s\n' "$HTTP_PORT"
  } > "$tmp_file"
  chmod 600 "$tmp_file"
  mv "$tmp_file" "$ENV_FILE"
  unset secret
else
  chmod 600 "$ENV_FILE"
fi

compose=(docker compose --project-name "$PROJECT_NAME" --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

log "Validating standalone Compose configuration"
"${compose[@]}" config --quiet

log "Building and starting the standalone ERP03 stack"
"${compose[@]}" up --build -d

log "Waiting for the API readiness endpoint"
ready=false
for attempt in $(seq 1 60); do
  if curl --silent --show-error --fail --max-time 5 "http://127.0.0.1:8000/api/v1/readyz" >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 2
done

if [[ "$ready" != true ]]; then
  "${compose[@]}" ps
  "${compose[@]}" logs --tail=100 migrate backend frontend
  die "ERP03 did not become ready. Data volumes were preserved for diagnosis."
fi

curl --silent --show-error --fail --max-time 5 "http://127.0.0.1:$HTTP_PORT/" >/dev/null \
  || die "Frontend HTTP smoke test failed."

log "Standalone ERP03 is ready"
printf 'Frontend: http://localhost:%s\n' "$HTTP_PORT"
printf 'API docs: http://localhost:8000/docs\n'
printf 'API readiness: http://localhost:8000/api/v1/readyz\n'
printf 'Environment: %s (mode 600)\n' "$ENV_FILE"
printf '\nStop without deleting data:\n'
printf 'docker compose --project-name %s --env-file %s -f %s down\n' \
  "$PROJECT_NAME" "$ENV_FILE" "$COMPOSE_FILE"
