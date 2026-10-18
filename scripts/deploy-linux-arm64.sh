#!/usr/bin/env bash
# Deploy a previously qualified ERP03 revision to Debian/Ubuntu Linux ARM64.
# Requires a dedicated, restricted production runner and pre-provisioned secrets.
set -Eeuo pipefail
umask 027

readonly ROOT=/opt/erp03
readonly RELEASES="$ROOT/releases"
readonly ENV_FILE=/etc/erp03/erp03.env
readonly SERVICE_FILE=/etc/systemd/system/erp03-backend.service
readonly NGINX_FILE=/etc/nginx/sites-available/erp03
readonly NGINX_ENABLED=/etc/nginx/sites-enabled/erp03
switched=0
deploy_success=0
old_target=""

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
log() { printf '\n[erp03-deploy] %s\n' "$*"; }

rollback_on_error() {
  rc=$?
  if [[ "$deploy_success" != "1" && "$switched" == "1" ]]; then
    printf '\n[erp03-deploy] deployment failed; restoring previous code release\n' >&2
    if [[ -n "$old_target" ]]; then
      ln -sfn "$old_target" "$ROOT/current.rollback"
      mv -Tf "$ROOT/current.rollback" "$ROOT/current"
      systemctl restart erp03-backend.service || true
    else
      rm -f "$ROOT/current"
      systemctl stop erp03-backend.service || true
    fi
    systemctl reload nginx || true
  fi
  exit "$rc"
}
trap rollback_on_error EXIT

[[ "$(id -u)" -eq 0 ]] || die "must run as root"
[[ $# -eq 1 ]] || die "usage: deploy-linux-arm64.sh <40-character-git-sha>"
readonly SHA="$1"
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || die "invalid commit SHA"
case "$(uname -m)" in aarch64|arm64) ;; *) die "Linux ARM64 required; found $(uname -m)" ;; esac

for cmd in python3 node npm systemctl nginx curl runuser; do
  command -v "$cmd" >/dev/null 2>&1 || die "required command missing: $cmd"
done
[[ -f "$ENV_FILE" ]] || die "create $ENV_FILE from deploy/erp03.env.example before deployment"
[[ -d /etc/nginx/sites-available && -d /etc/nginx/sites-enabled ]] || die "nginx sites directories missing"
grep -q '^SECRET_KEY=.\+' "$ENV_FILE" || die "SECRET_KEY is missing from $ENV_FILE"
grep -q '^DATABASE_URL=.\+' "$ENV_FILE" || die "DATABASE_URL is missing from $ENV_FILE"
grep -q '^CORS_ORIGINS=.\+' "$ENV_FILE" || die "CORS_ORIGINS is missing from $ENV_FILE"

if ! id erp03 >/dev/null 2>&1; then
  useradd --system --home-dir "$ROOT" --create-home --shell /usr/sbin/nologin erp03
fi
install -d -o root -g erp03 -m 0750 "$ROOT" "$RELEASES" /etc/erp03
chown root:erp03 "$ENV_FILE"
chmod 0640 "$ENV_FILE"

readonly SOURCE_DIR="\${SOURCE_DIR:-}"
[[ -n "$SOURCE_DIR" && -f "$SOURCE_DIR/ERP-BACKEND/requirements.txt" ]] || die "SOURCE_DIR must contain the downloaded ERP03 source"
readonly RELEASE="$RELEASES/$SHA"
[[ ! -e "$RELEASE" ]] || die "release already exists: $RELEASE (immutable releases are not overwritten)"

log "Stage immutable release $SHA"
install -d -o erp03 -g erp03 -m 0750 "$RELEASE"
cp -a "$SOURCE_DIR/." "$RELEASE/"
chown -R erp03:erp03 "$RELEASE"

log "Install backend dependencies"
runuser -u erp03 -- python3 -m venv "$RELEASE/venv"
runuser -u erp03 -- "$RELEASE/venv/bin/python" -m pip install --disable-pip-version-check --no-cache-dir -r "$RELEASE/ERP-BACKEND/requirements.txt"

log "Build frontend assets for the target host"
cd "$RELEASE/frontend"
runuser -u erp03 -- npm install --no-audit --no-fund
runuser -u erp03 -- npm run build
[[ -s "$RELEASE/frontend/dist/index.html" ]] || die "frontend build did not produce dist/index.html"

# Extract DATABASE_URL as data, never source/execute the environment file.
DATABASE_URL="$(sed -n 's/^DATABASE_URL=//p' "$ENV_FILE" | head -n 1)"
[[ -n "$DATABASE_URL" ]] || die "DATABASE_URL is empty"
log "Run forward migrations before switching application code"
(
  cd "$RELEASE/ERP-BACKEND"
  runuser -u erp03 -- env DATABASE_URL="$DATABASE_URL" \
    "$RELEASE/venv/bin/alembic" upgrade head
)

log "Install systemd and nginx integration"
cat > "$SERVICE_FILE" <<'UNIT'
[Unit]
Description=ERP03 FastAPI backend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=erp03
Group=erp03
WorkingDirectory=/opt/erp03/current/ERP-BACKEND
EnvironmentFile=/etc/erp03/erp03.env
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/erp03/current/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=3
TimeoutStartSec=45
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/erp03 /var/lib/erp03
UMask=0027

[Install]
WantedBy=multi-user.target
UNIT

cat > "$NGINX_FILE" <<'NGINX'
server {
    listen 80;
    server_name _;
    root /opt/erp03/current/frontend/dist;
    index index.html;
    server_tokens off;
    client_max_body_size 10m;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 5s;
        proxy_read_timeout 60s;
    }

    location /metrics {
        allow 127.0.0.1;
        deny all;
        proxy_pass http://127.0.0.1:8000/metrics;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
NGINX
ln -sfn "$NGINX_FILE" "$NGINX_ENABLED"
nginx -t

old_target="$(readlink "$ROOT/current" 2>/dev/null || true)"
ln -s "$RELEASE" "$ROOT/current.new"
mv -Tf "$ROOT/current.new" "$ROOT/current"
switched=1

systemctl daemon-reload
systemctl enable erp03-backend.service
systemctl restart erp03-backend.service
systemctl reload nginx

log "Wait for API health endpoint"
healthy=0
for _ in $(seq 1 30); do
  if curl --fail --silent --show-error --max-time 3 http://127.0.0.1:8000/api/v1/healthz >/dev/null 2>&1; then
    healthy=1
    break
  fi
  sleep 2
done
[[ "$healthy" == "1" ]] || die "API health check failed; automatic code rollback will run"

deploy_success=1
log "Deployment successful: $SHA"
log "Previous code release: \${old_target:-none}"
log "Schema migrations are forward-only; database rollback is deliberately not automated."
