# ERP03 Development Workspace

This directory is the single development-environment entry point for local Dev Containers and GitHub Codespaces on `feat/erpnext-isolated`.

## Workspace layout

- `ERP-BACKEND/` — FastAPI backend, Alembic migrations, Celery worker
- `frontend/` — React + Vite frontend
- `Dockerfile.erpnext` — ERPNext production image build
- `docker-compose.yml` — production-oriented local service topology
- `.github/workflows/` — CI and ERPNext image workflows
- `.devcontainer/` — reproducible developer workstation definition

## Pre-installed toolchain

- Python 3.11
- Node.js 22 / npm
- Docker CLI with host Docker socket integration
- GitHub CLI
- VS Code Python, Pylance, Ruff/Black, Docker, ESLint, Prettier, YAML, GitLens and GitHub Actions extensions

Python dependencies are installed from `ERP-BACKEND/requirements.txt`; frontend dependencies are installed from `frontend/package.json` during Codespace/Dev Container creation.

## Principles

1. Development tooling is isolated from production runtime images.
2. The repository remains the source of truth for the workspace definition.
3. No production secrets are copied into the development container.
4. Codespaces and local Dev Containers use the same `.devcontainer/devcontainer.json` definition.
5. Production deployment remains governed by the existing CI/GitOps configuration; this workspace does not replace it.
