# ERP03 GitHub Webhook → Remote Deployment

This receiver is intentionally host-level: it does not run inside the ERP backend container. The remote server receives GitHub's signed webhook, accepts only a successful `workflow_run` for the `Container Build and Publish` workflow on `main`, then updates `/opt/erp03` and pulls the exact commit-tagged ERP03 images from GHCR.

## Remote server setup

Assume the repository is deployed at `/opt/erp03` and the service account is `erpdeploy`.

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin erpdeploy || true
sudo usermod -aG docker erpdeploy
sudo mkdir -p /opt/erp03 /etc/erp03
sudo chown -R erpdeploy:erpdeploy /opt/erp03
cd /opt/erp03
sudo -u erpdeploy git clone https://github.com/nyeinpyaesone-ui/ERP03.git .
```

Install the receiver environment:

```bash
sudo cp ops/github-webhook/github-webhook.env.example /etc/erp03/github-webhook.env
sudo chmod 600 /etc/erp03/github-webhook.env
sudoedit /etc/erp03/github-webhook.env
```

Set a long random `GITHUB_WEBHOOK_SECRET`. The same secret must be entered in the GitHub repository webhook configuration. Configure the least-privilege GHCR credentials documented in the environment example when the packages are private.

Install and start systemd:

```bash
sudo cp ops/github-webhook/github-webhook.service /etc/systemd/system/github-webhook.service
sudo chmod +x /opt/erp03/ops/github-webhook/deploy-from-github.sh
sudo systemctl daemon-reload
sudo systemctl enable --now github-webhook
sudo systemctl status github-webhook
```

The receiver listens only on `127.0.0.1:9001`; do not expose port 9001 directly to the Internet.

## Nginx reverse proxy

Inside the HTTPS `server` that serves `erp.anynoob.com`, add:

```nginx
location = /github/webhook {
    proxy_pass http://127.0.0.1:9001/github/webhook;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Then reload Nginx.

## GitHub webhook

Repository: `nyeinpyaesone-ui/ERP03`

Payload URL:

`https://erp.anynoob.com/github/webhook`

Content type: `application/json`

Secret: the same value as `GITHUB_WEBHOOK_SECRET`

SSL verification: enabled

Events: `Workflow runs`

The receiver deploys only when the workflow run is `completed`, `success`, its branch is `main`, and its workflow name is `Container Build and Publish`. This prevents deployment from CodeQL, security, or release workflows that do not publish the main commit images.

## Deployment path

```text
GitHub ERP03
    │ workflow_run: Container Build and Publish / completed + success
    ▼
https://erp.anynoob.com/github/webhook
    │ HMAC SHA-256 verification
    ▼
127.0.0.1:9001 webhook receiver
    │
    ▼
/opt/erp03/ops/github-webhook/deploy-from-github.sh
    │
    ├─ git fetch origin main
    ├─ reset local checkout to origin/main
    ├─ derive exact Git SHA
    ├─ docker login ghcr.io
    ├─ docker compose pull erp-backend frontend
    ├─ docker compose up -d --remove-orphans
    └─ GET http://127.0.0.1:8000/health
```
