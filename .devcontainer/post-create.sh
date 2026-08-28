#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python -m pip install --upgrade pip
python -m pip install -r ERP-BACKEND/requirements.txt

if [[ -f frontend/package-lock.json ]]; then
  npm --prefix frontend ci
elif [[ -f frontend/package.json ]]; then
  npm --prefix frontend install
fi

git config --global --add safe.directory "$ROOT"

echo "ERP03 development workspace ready."
echo "Backend:  ERP-BACKEND"
echo "Frontend: frontend"
echo "Branch:   $(git branch --show-current)"
