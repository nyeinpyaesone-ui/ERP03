#!/usr/bin/env bash
set -euo pipefail

echo "Setting up ERP03 dev environment..."

# Use the main setup script for full configuration
if [ -f scripts/setup.sh ]; then
  bash scripts/setup.sh --skip-frontend --env-type development
else
  echo "Warning: scripts/setup.sh not found, falling back to manual setup"
  if [ -d ERP-BACKEND ]; then
    echo "Installing backend dependencies..."
    pushd ERP-BACKEND > /dev/null
    python -m pip install --upgrade pip
    if [ -f requirements.txt ]; then
      pip install -r requirements.txt
    fi
    if [ -f dev-requirements.txt ]; then
      pip install -r dev-requirements.txt
    fi
    popd > /dev/null
  fi
fi

# Install frontend dependencies
if [ -d frontend ]; then
  echo "Installing frontend dependencies..."
  pushd frontend > /dev/null
  if [ -f package.json ]; then
    npm ci --no-audit --no-fund || npm install
  fi
  popd > /dev/null
fi

echo "Devcontainer setup complete."
echo "Run 'cd ERP-BACKEND && pytest -q' to verify backend tests."
echo "Run 'cd frontend && npm run build' to verify frontend build."