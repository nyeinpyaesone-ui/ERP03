#!/usr/bin/env bash
set -euo pipefail

echo "Setting up ERP03 dev environment..."

if [ -d ERP-BACKEND ]; then
  echo "Installing backend dependencies..."
  pushd ERP-BACKEND > /dev/null
  python -m pip install --upgrade pip
  if [ -f requirements.txt ]; then
    pip install -r requirements.txt
  else
    echo "Warning: ERP-BACKEND/requirements.txt not found"
  fi
  popd > /dev/null
fi

if [ -d frontend ]; then
  echo "Installing frontend dependencies..."
  pushd frontend > /dev/null
  if [ -f package.json ]; then
    npm ci || npm install
  else
    echo "Warning: frontend/package.json not found"
  fi
  popd > /dev/null
fi

echo "Devcontainer setup complete."
