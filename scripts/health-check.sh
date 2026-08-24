#!/usr/bin/env bash
set -e

C='\033[0;36m'; G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; NC='\033[0m'; BD='\033[1m'
info(){ echo -e "${C}[INFO]${NC} $1"; }
ok(){ echo -e "${G}[PASS]${NC} $1"; }
warn(){ echo -e "${Y}[WARN]${NC} $1"; }
err(){ echo -e "${R}[FAIL]${NC} $1"; }

echo -e "${BD}${C}ERP03 — Health Check${NC}"

info "[1/8] Git repository"
if [ -d .git ]; then ok "Git OK — $(git rev-list --count HEAD 2>/dev/null || echo 0) commits"; else err "Git repository not found"; fi

info "[2/8] Docker"
if command -v docker >/dev/null 2>&1; then ok "Docker OK — $(docker --version)"; else warn "Docker not installed"; fi

info "[3/8] Docker Compose"
if docker compose version >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1; then ok "Docker Compose OK"; else warn "Docker Compose not found"; fi

info "[4/8] Python"
if command -v python3 >/dev/null 2>&1; then ok "Python OK — $(python3 --version)"; else warn "Python 3 not installed"; fi

info "[5/8] Runtime environment"
if [ -f "ERP-BACKEND/.env" ]; then ok "ERP-BACKEND/.env exists"; elif [ -f "ERP-BACKEND/.env.example" ]; then warn "ERP-BACKEND/.env missing (copy from .env.example)"; else warn "ERP-BACKEND environment template not found"; fi

info "[6/8] Architecture boundaries"
for dir in ERP-BACKEND AI-BACKEND INTEGRATION INFRASTRUCTURE docs; do
  if [ -d "$dir" ]; then ok "$dir/ exists"; else err "$dir/ missing"; fi
done

info "[7/8] Canonical files"
for file in README.md docker-compose.yml Makefile CONTRIBUTING.md CHANGELOG.md docs/architecture/BOUNDARIES.md; do
  if [ -f "$file" ]; then ok "$file exists"; else err "$file missing"; fi
done

info "[8/8] GitHub remote"
if git remote get-url origin >/dev/null 2>&1; then ok "Remote configured — $(git remote get-url origin)"; else warn "GitHub remote not configured"; fi

echo -e "${BD}${G}Health check complete.${NC}"
