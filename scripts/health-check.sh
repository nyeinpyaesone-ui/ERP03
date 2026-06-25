#!/usr/bin/env bash
###############################################################################
# ERP SOLUTION — Health Check Dashboard
# Usage: ./scripts/health-check.sh
###############################################################################

set -e

C='[0;36m'; G='[0;32m'; Y='[1;33m'; R='[0;31m'; NC='[0m'; BD='[1m'

info()  { echo -e "${C}[INFO]${NC} $1"; }
ok()    { echo -e "${G}[PASS]${NC} $1"; }
warn()  { echo -e "${Y}[WARN]${NC} $1"; }
err()   { echo -e "${R}[FAIL]${NC} $1"; }

echo ""
echo -e "${C}══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BD}${C}  ERP SOLUTION — Health Check Dashboard${NC}"
echo -e "${C}══════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check 1: Git Repository
info "[1/10] Checking Git repository..."
if [ -d ".git" ]; then
    commits=$(git rev-list --count HEAD 2>/dev/null || echo "0")
    files=$(git ls-files | wc -l | tr -d ' ')
    branch=$(git branch --show-current 2>/dev/null || echo "N/A")
    ok "Git OK — ${commits} commits, ${files} files, branch: ${branch}"
else
    err "Git repository not found"
fi

# Check 2: Docker
info "[2/10] Checking Docker..."
if command -v docker &>/dev/null; then
    version=$(docker --version | awk '{print $3}' | tr -d ',')
    ok "Docker OK — ${version}"
else
    warn "Docker not installed"
fi

# Check 3: Docker Compose
info "[3/10] Checking Docker Compose..."
if command -v docker-compose &>/dev/null || docker compose version &>/dev/null; then
    ok "Docker Compose OK"
else
    warn "Docker Compose not found"
fi

# Check 4: Node.js
info "[4/10] Checking Node.js..."
if command -v node &>/dev/null; then
    version=$(node --version)
    ok "Node.js OK — ${version}"
else
    warn "Node.js not installed"
fi

# Check 5: Python
info "[5/10] Checking Python..."
if command -v python3 &>/dev/null; then
    version=$(python3 --version)
    ok "Python OK — ${version}"
else
    warn "Python 3 not installed"
fi

# Check 6: Backend Environment
info "[6/10] Checking backend environment..."
if [ -f "backend/.env" ]; then
    ok "Backend .env exists"
elif [ -f "backend/.env.example" ]; then
    warn "Backend .env missing (copy from .env.example)"
else
    warn "Backend .env not found"
fi

# Check 7: Frontend Environment
info "[7/10] Checking frontend environment..."
if [ -f "frontend/.env" ]; then
    ok "Frontend .env exists"
elif [ -f "frontend/.env.example" ]; then
    warn "Frontend .env missing (copy from .env.example)"
else
    warn "Frontend .env not found"
fi

# Check 8: Key Files
info "[8/10] Checking key files..."
key_files=("README.md" "docker-compose.yml" "Makefile" "CONTRIBUTING.md" "CHANGELOG.md")
missing=0
for file in "${key_files[@]}"; do
    if [ -f "$file" ]; then
        ok "${file} exists"
    else
        err "${file} missing"
        ((missing++))
    fi
done

# Check 9: Module Directories
info "[9/10] Checking module directories..."
modules=("backend" "frontend" "mobile" "infra" "docs" "scripts")
for mod in "${modules[@]}"; do
    if [ -d "$mod" ]; then
        count=$(find "$mod" -type f | wc -l | tr -d ' ')
        ok "${mod}/ — ${count} files"
    else
        warn "${mod}/ not found"
    fi
done

# Check 10: GitHub Remote
info "[10/10] Checking GitHub remote..."
if git remote get-url origin &>/dev/null; then
    remote=$(git remote get-url origin)
    ok "Remote configured — ${remote}"
else
    warn "GitHub remote not configured"
fi

# Summary
echo ""
echo -e "${C}══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BD}${C}  Health Check Summary${NC}"
echo -e "${C}══════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Run 'make dev' to start development environment"
echo "  Run './scripts/gh-manager.sh verify' for full verification"
echo "  Visit https://github.com/nyeinpyaesone-ui/ERP for repository"
echo ""
echo -e "${C}══════════════════════════════════════════════════════════════════${NC}"
