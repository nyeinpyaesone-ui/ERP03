#!/usr/bin/env bash
###############################################################################
# ERP SOLUTION — Backup Script
# Usage: ./scripts/backup.sh [output_dir]
###############################################################################

set -e

OUTPUT_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="erp_backup_${TIMESTAMP}"
BACKUP_PATH="${OUTPUT_DIR}/${BACKUP_NAME}"

echo "=========================================="
echo "  ERP SOLUTION Backup"
echo "=========================================="
echo "  Destination: ${BACKUP_PATH}"
echo ""

mkdir -p "${BACKUP_PATH}"

# Backup source code (excluding .git and node_modules)
echo "[1/4] Backing up source code..."
tar -czf "${BACKUP_PATH}/source_code.tar.gz"     --exclude='.git'     --exclude='node_modules'     --exclude='venv'     --exclude='__pycache__'     --exclude='*.pyc'     .
echo "  ✓ Source code backed up"

# Backup database (if running)
echo "[2/4] Backing up database..."
if docker-compose ps postgres &>/dev/null; then
    docker-compose exec -T postgres pg_dump -U erp erp_solution > "${BACKUP_PATH}/database.sql"
    echo "  ✓ Database backed up"
else
    echo "  ! PostgreSQL not running, skipping database backup"
fi

# Backup environment files
echo "[3/4] Backing up environment files..."
if [ -f "backend/.env" ]; then
    cp backend/.env "${BACKUP_PATH}/backend.env"
fi
if [ -f "frontend/.env" ]; then
    cp frontend/.env "${BACKUP_PATH}/frontend.env"
fi
echo "  ✓ Environment files backed up"

# Create backup manifest
echo "[4/4] Creating backup manifest..."
cat > "${BACKUP_PATH}/manifest.txt" << EOF
ERP SOLUTION Backup
======================
Date: $(date)
Version: $(git describe --tags --always 2>/dev/null || echo "unknown")
Commit: $(git rev-parse HEAD 2>/dev/null || echo "unknown")
Branch: $(git branch --show-current 2>/dev/null || echo "unknown")

Contents:
- source_code.tar.gz (full source)
- database.sql (PostgreSQL dump)
- backend.env (backend configuration)
- frontend.env (frontend configuration)
EOF
echo "  ✓ Manifest created"

echo ""
echo "=========================================="
echo "  Backup Complete!"
echo "  Location: ${BACKUP_PATH}"
echo "=========================================="
