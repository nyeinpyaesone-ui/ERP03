#!/usr/bin/env bash
set -Eeuo pipefail

BENCH=/home/frappe/frappe-bench
SITE_NAME=${SITE_NAME:?SITE_NAME is required}
DB_HOST=${DB_HOST:?DB_HOST is required}
DB_PORT=${DB_PORT:-3306}
DB_ROOT_USER=${DB_ROOT_USER:-root}
REDIS_CACHE=${REDIS_CACHE:?REDIS_CACHE is required}
REDIS_QUEUE=${REDIS_QUEUE:?REDIS_QUEUE is required}
REDIS_SOCKETIO=${REDIS_SOCKETIO:?REDIS_SOCKETIO is required}

cd "$BENCH"

wait_for_tcp() {
  local host="$1" port="$2" name="$3"
  python - "$host" "$port" "$name" <<'PY'
import socket, sys, time
host, port, name = sys.argv[1], int(sys.argv[2]), sys.argv[3]
deadline = time.monotonic() + 120
while time.monotonic() < deadline:
    try:
        with socket.create_connection((host, port), timeout=3):
            print(f"[erpnext] {name} reachable at {host}:{port}")
            raise SystemExit(0)
    except OSError:
        time.sleep(2)
print(f"[erpnext] timeout waiting for {name} at {host}:{port}", file=sys.stderr)
raise SystemExit(1)
PY
}

redis_endpoint() {
  python - "$1" <<'PY'
from urllib.parse import urlparse
import sys
value = sys.argv[1]
p = urlparse(value if "://" in value else f"redis://{value}")
print(p.hostname or "")
print(p.port or 6379)
PY
}

redis_url() {
  case "$1" in
    *://*) printf '%s' "$1" ;;
    *) printf 'redis://%s' "$1" ;;
  esac
}

REDIS_CACHE_URL=$(redis_url "$REDIS_CACHE")
REDIS_QUEUE_URL=$(redis_url "$REDIS_QUEUE")
REDIS_SOCKETIO_URL=$(redis_url "$REDIS_SOCKETIO")
export REDIS_CACHE_URL REDIS_QUEUE_URL REDIS_SOCKETIO_URL

wait_for_tcp "$DB_HOST" "$DB_PORT" "database"
read -r CACHE_HOST CACHE_PORT < <(redis_endpoint "$REDIS_CACHE_URL" | paste -sd ' ' -)
read -r QUEUE_HOST QUEUE_PORT < <(redis_endpoint "$REDIS_QUEUE_URL" | paste -sd ' ' -)
read -r SOCKETIO_HOST SOCKETIO_PORT < <(redis_endpoint "$REDIS_SOCKETIO_URL" | paste -sd ' ' -)
wait_for_tcp "$CACHE_HOST" "$CACHE_PORT" "redis-cache"
wait_for_tcp "$QUEUE_HOST" "$QUEUE_PORT" "redis-queue"
wait_for_tcp "$SOCKETIO_HOST" "$SOCKETIO_PORT" "redis-socketio"

mkdir -p sites logs

python - "$BENCH/sites/common_site_config.json" <<'PY'
import json, os, pathlib, sys
path = pathlib.Path(sys.argv[1])
try:
    config = json.loads(path.read_text()) if path.exists() else {}
except json.JSONDecodeError:
    config = {}
config.update({
    "db_host": os.environ["DB_HOST"],
    "db_port": int(os.environ.get("DB_PORT", "3306")),
    "redis_cache": os.environ["REDIS_CACHE_URL"],
    "redis_queue": os.environ["REDIS_QUEUE_URL"],
    "redis_socketio": os.environ["REDIS_SOCKETIO_URL"],
    "socketio_port": 9000,
})
path.write_text(json.dumps(config, indent=2) + "\n")
PY

if [[ ! -f "sites/$SITE_NAME/site_config.json" ]]; then
  : "${DB_ROOT_PASSWORD:?DB_ROOT_PASSWORD is required for first-time site creation}"
  : "${ADMIN_PASSWORD:?ADMIN_PASSWORD is required for first-time site creation}"
  bench new-site "$SITE_NAME" \
    --db-host "$DB_HOST" \
    --db-port "$DB_PORT" \
    --db-root-username "$DB_ROOT_USER" \
    --db-root-password "$DB_ROOT_PASSWORD" \
    --admin-password "$ADMIN_PASSWORD" \
    --no-mariadb-socket \
    --install-app erpnext
fi

GUNICORN_WORKERS=${GUNICORN_WORKERS:-2}
GUNICORN_THREADS=${GUNICORN_THREADS:-4}
GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-120}
QUEUE=${QUEUE:-long,default,short}
PIDS=()
cleanup() {
  trap - TERM INT EXIT
  for pid in "${PIDS[@]:-}"; do kill -TERM "$pid" 2>/dev/null || true; done
  for pid in "${PIDS[@]:-}"; do wait "$pid" 2>/dev/null || true; done
}
trap cleanup TERM INT EXIT

start_processes() {
  "$BENCH/env/bin/gunicorn" --chdir="$BENCH/sites" --bind=0.0.0.0:8000 \
    --threads="$GUNICORN_THREADS" --workers="$GUNICORN_WORKERS" --worker-class=gthread \
    --worker-tmp-dir=/dev/shm --timeout="$GUNICORN_TIMEOUT" --preload frappe.app:application &
  PIDS+=("$!")
  node "$BENCH/apps/frappe/socketio.js" & PIDS+=("$!")
  bench schedule & PIDS+=("$!")
  bench worker --queue "$QUEUE" & PIDS+=("$!")
}

case "${1:-start}" in
  migrate) exec bench --site "$SITE_NAME" migrate ;;
  backup) exec bench --site "$SITE_NAME" backup --with-files ;;
  start)
    start_processes
    while :; do
      for pid in "${PIDS[@]}"; do
        if ! kill -0 "$pid" 2>/dev/null; then wait "$pid" || true; exit 1; fi
      done
      sleep 5
    done
    ;;
  *) exec "$@" ;;
esac
