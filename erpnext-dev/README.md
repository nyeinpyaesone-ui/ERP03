# ERPNext Development Workspace

This directory contains a complete, ready-to-use ERPNext v16.31.1 development environment extracted from the ERP03 production configuration.

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
cd /workspace/erpnext-dev
./quickstart.sh
```

This script will:
1. Check prerequisites (Docker, Docker Compose, Git)
2. Clone the official Frappe Docker repository
3. Configure the environment with development settings
4. Build a custom ERPNext image with your apps
5. Start all services
6. Create a new site and install ERPNext
7. Configure local DNS

### Option 2: Manual Setup

Follow the detailed instructions in `SETUP_GUIDE.md`.

## Files Included

| File | Description |
|------|-------------|
| `README.md` | This file - quick overview |
| `SETUP_GUIDE.md` | Comprehensive setup and troubleshooting guide |
| `quickstart.sh` | Automated setup script |
| `docker-compose.dev.yaml` | Docker Compose configuration for development |
| `.env.example` | Environment variable template |
| `apps.json` | Application sources configuration |

## Extracted Configuration Data

### Versions
- **ERPNext**: v16.31.1
- **Frappe**: version-16
- **Frappe Docker**: v3.2.1

### Default Credentials (Development Only!)
- **Site URL**: http://erp.localhost:8000
- **Username**: Administrator
- **Password**: admin123
- **Database Password**: development_password_123

⚠️ **WARNING**: These are development defaults. Change them for any production or staging environment!

## Prerequisites

- Docker 20.10+
- Docker Compose V2+
- Git
- 8GB+ RAM recommended
- 50GB+ free disk space

## Architecture

This development environment uses the **official Frappe Docker production architecture** with:

- MariaDB 10.6 for database
- Redis for cache, queue, and socketio
- Gunicorn backend workers
- Nginx frontend
- WebSocket server for realtime events
- Scheduler for background jobs

## Common Commands

```bash
# Start all services
docker compose -f docker-compose.dev.yaml up -d

# View logs
docker compose -f docker-compose.dev.yaml logs -f

# Stop all services
docker compose -f docker-compose.dev.yaml down

# Open bench console
docker compose exec backend bench --site erp.localhost console

# Run bench commands
docker compose exec backend bench --site erp.localhost migrate
docker compose exec backend bench --site erp.localhost clear-cache

# Backup site
docker compose exec backend bench --site erp.localhost backup

# Restore from backup
docker compose exec backend bench --site erp.localhost restore /path/to/backup.sql.gz
```

## Adding Custom Apps

1. Add your app to `apps.json`:
```json
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-16"
  },
  {
    "url": "https://github.com/your-org/your_custom_app",
    "branch": "main"
  }
]
```

2. Rebuild the image:
```bash
cd frappe_docker
DOCKER_BUILDKIT=1 docker build \
  --file images/layered/Containerfile \
  --tag erp03-erpnext:dev \
  --build-arg FRAPPE_BRANCH=version-16 \
  --secret id=apps_json,src=../apps.json \
  .
```

3. Restart services and install the app:
```bash
docker compose restart
docker compose exec backend bench --site erp.localhost install-app your_custom_app
```

## Troubleshooting

See the comprehensive troubleshooting section in `SETUP_GUIDE.md`.

Quick fixes:

```bash
# Reset everything
docker compose down -v
docker system prune -f
./quickstart.sh --resume

# Check service health
docker compose ps

# View specific service logs
docker compose logs backend
docker compose logs db
```

## Production Deployment

For production deployment, refer to:
- `/workspace/infra/erpnext/` - Production configuration
- `/workspace/infra/erpnext/gitops/` - Kubernetes manifests
- `/workspace/.github/workflows/erpnext-production.yml` - CI/CD pipeline

## Next Steps

1. ✅ Complete the quickstart setup
2. 📚 Review `SETUP_GUIDE.md` for detailed information
3. 🔧 Customize `.env` for your needs
4. 🧪 Run the verification checklist from `SETUP_GUIDE.md`
5. 📝 Address P0/P1 items from `IMPLEMENTATION-TASKS.md` before UAT

## Support Resources

- [Official Frappe Docker](https://github.com/frappe/frappe_docker)
- [ERPNext Documentation](https://docs.erpnext.com)
- [Frappe Framework Docs](https://frappeframework.com/docs)
- [Community Forum](https://discuss.frappe.io)

---

**Note**: This workspace was created by extracting configuration from the ERP03 repository's `feat/erpnext-production` branch. All original source files remain in their respective locations within `/workspace`.
