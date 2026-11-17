# Changelog

All notable changes to ERP03 are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Redis-backed rate limiter (`RedisRateLimitMiddleware`) with ZSET sliding window
- Devcontainer with Docker Compose (app + PostgreSQL + Redis)
- CI workflow for building/pushing dev images to Docker Hub
- `doctor.sh` health check script with venv path and docker daemon checks
- AGENTS.md comprehensive developer instructions
- SECURITY.md, .editorconfig, issue templates, pre-commit config

### Fixed
- `doctor.sh` venv path resolution (root `.venv` vs `ERP-BACKEND/.venv`)
- `doctor.sh` docker compose availability check (daemon may not be running)
- Rate limiter trusted-proxy XFF resolution and 429 threshold tests

### Changed
- CI pipeline: PostgreSQL + Redis service containers with health checks
- Frontend build: `VITE_API_BASE_URL=/api` build arg for nginx proxy

## [1.0.0] - 2026-10-30

### Added
- Initial modular monolith: FastAPI backend + React/Vite frontend
- POS sale idempotency with SHA-256 fingerprint
- Cross-module operation orchestration (6-state machine)
- TypeSafe System One integration (optional)
- Terraform infrastructure modules (AWS/GCP/Azure)
- Comprehensive test suite (57 tests, 1 PG-only skip)
