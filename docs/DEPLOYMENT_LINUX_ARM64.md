# ERP03 Linux ARM64 deployment

## Supported target

- Debian/Ubuntu Linux on `aarch64` / `arm64`.
- Python 3.12 or newer and Node.js 22 or newer on the target.
- systemd, nginx, curl, and npm must already be installed.
- A production database must be provisioned and backed up separately.
- Deployment is native on ARM64; no Docker daemon is required on the target.

## CI/CD model

1. Pull requests and pushes run one consolidated workflow on GitHub's native `ubuntu-24.04-arm` runner.
2. Qualification downloads the exact event commit using the GitHub API and `GITHUB_TOKEN`; it does not use third-party `uses:` actions. It checks architecture/runtime, backend lint/format/compile, PostgreSQL migrations/tests, frontend build, Python dependency audit, and native ARM64 container builds.
3. Production deployment is opt-in via `workflow_dispatch` and requires the protected GitHub `production` environment plus a dedicated self-hosted runner labelled `Linux`, `ARM64`, and `erp03-production`.
4. The production runner must be a dedicated machine, not shared with untrusted pull-request jobs. Restrict runner group access to this repository and protect the production environment with required reviewers.
5. The deployment script creates an immutable release directory, installs dependencies, builds frontend assets, runs forward migrations, switches the `current` symlink, restarts systemd, and checks API health. A failed health check restores the prior code symlink.

## One-time host preparation

Install Python 3.12+, Node.js 22+, npm, nginx, systemd, curl, and a GitHub Actions self-hosted runner on the ARM64 host. Register the runner with labels `Linux`, `ARM64`, `erp03-production`; configure it to run as a dedicated restricted account. The deployment job uses passwordless sudo only for the deployment script, so configure a narrowly scoped sudoers rule for that script rather than granting general sudo to arbitrary runner jobs.

Provision PostgreSQL and a dedicated least-privilege database role. Apply network firewall rules so PostgreSQL is not exposed publicly. Create the runtime configuration:

```bash
sudo install -d -o root -g root -m 0750 /etc/erp03
sudo install -o root -g root -m 0600 deploy/erp03.env.example /etc/erp03/erp03.env
sudoedit /etc/erp03/erp03.env
sudo chown root:root /etc/erp03/erp03.env
sudo chmod 0600 /etc/erp03/erp03.env
```

Replace all placeholders. Set `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`, and `PUBLIC_HOSTNAME` to real production values. `PUBLIC_HOSTNAME` must be the DNS hostname routed to this nginx instance. Never commit the production environment file. The deployment script adjusts the environment file to root:erp03 mode 0640 after checking it.

## Runbook

- PR/push qualification: automatic.
- Production release: GitHub Actions → ERP03 Linux ARM64 CI/CD → Run workflow → choose the reviewed commit on `main` → set `deploy_production=true`. The deploy job only runs after the same workflow's qualification job passes.
- Verify `systemctl status erp03-backend`, `journalctl -u erp03-backend -n 200 --no-pager`, `nginx -t`, and `curl -fsS http://127.0.0.1:8000/api/v1/healthz`.
- Keep database backups and verify restore procedures before the first production deployment.
- Configure HTTPS at a trusted reverse proxy or install and validate TLS for nginx before exposing this service to the public internet. The included nginx site is an HTTP reverse-proxy/static-serving baseline, not a TLS configuration.

## Rollback boundary

Application code rollback is automatic if the post-switch health check fails. Database migrations are forward-only and are **not** automatically reversed. Use expand/contract migrations and keep each release compatible with the previous schema; restore a database backup only under an approved recovery procedure. The previous release directory is retained for operator-led rollback.

## Known prerequisites and limits

- GitHub must allow native GitHub-hosted ARM64 runners for this repository/plan.
- The repository must permit the built-in `GITHUB_TOKEN` to read the repository tarball.
- Production requires a configured self-hosted ARM64 runner and protected `production` environment. Without them, CI can qualify but deployment will remain queued/unavailable.
- This change intentionally removes the seven previous workflow files and consolidates their checks. It does not silently disable failing gates with `|| true`.
