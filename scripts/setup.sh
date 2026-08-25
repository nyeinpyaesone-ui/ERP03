#!/usr/bin/env bash
###############################################################################
# ERP SOLUTION — Environment Setup
# Run this after cloning the repository
###############################################################################

set -e

C='[0;36m'; G='[0;32m'; Y='[1;33m'; NC='[0m'

info()  { echo -e "${C}[i]${NC} $1"; }
ok()    { echo -e "${G}[✓]${NC} $1"; }
warn()  { echo -e "${Y}[!]${NC} $1"; }

echo "=========================================="
echo "  ERP SOLUTION Environment Setup"
echo "=========================================="
echo ""

# Check prerequisites
info "Checking prerequisites..."

for cmd in docker docker-compose git node npm python3 pip3; do
    if command -v "$cmd" &>/dev/null; then
        ok "$cmd found"
    else
        warn "$cmd not found (may be optional)"
    fi
done

echo ""

# Setup backend
if [ -d "backend" ]; then
    info "Setting up backend..."
    cd backend

    if [ ! -d "venv" ]; then
        python3 -m venv venv
        ok "Virtual environment created"
    fi

    source venv/bin/activate

    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        ok "Python dependencies installed"
    fi

    cd ..
fi

# Setup frontend
if [ -d "frontend" ]; then
    info "Setting up frontend..."
    cd frontend

    if [ -f "package.json" ]; then
        npm install
        ok "Node dependencies installed"
    fi

    cd ..
fi

# Setup mobile
if [ -d "mobile" ]; then
    info "Setting up mobile app..."
    cd mobile

    if [ -f "package.json" ]; then
        npm install
        ok "Mobile dependencies installed"
    fi

    cd ..
fi

# Create environment files
info "Creating environment files..."

if [ ! -f "backend/.env" ]; then
    cat > backend/.env << EOF
DATABASE_URL=postgresql://erp:erp_secret@localhost:5432/erp_solution
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-this-in-production-$(openssl rand -hex 16)
ENVIRONMENT=development
OLLAMA_URL=http://localhost:11434
EOF
    ok "backend/.env created"
fi

if [ ! -f "frontend/.env" ]; then
    cat > frontend/.env << EOF
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
EOF
    ok "frontend/.env created"
fi

echo ""
echo "=========================================="
echo "  ✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Start services:  docker-compose up -d"
echo "  2. Run backend:     cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  3. Run frontend:    cd frontend && npm run dev"
echo "  4. Run mobile:      cd mobile && npx expo start"
echo ""
echo "API docs: http://localhost:8000/docs"
echo ""
