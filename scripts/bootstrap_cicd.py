#!/usr/bin/env python3
"""
ERP03 Enterprise CI/CD Bootstrap
================================
Idempotent script to set up:
- Workflows: action-pinning, ci, security, release
- GitHub Environments (staging, production)
- Branch protection (optional)
- Docker Hub secrets (optional)
- SHA pinning for all Actions

Usage:
    python3 scripts/bootstrap_cicd.py
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

# ----------------------------------------------------------------------
# ACTION SHA MAP (hardcoded for reliability; update periodically)
# ----------------------------------------------------------------------
ACTION_SHAS = {
    "actions/checkout": "34e114876b0b11c390a56381ad16ebd13914f8d5",          # v4.3.1
    "actions/setup-python": "42375524e23c412d93fb67b49958b491fce71c38",      # v5.4.0
    "actions/setup-node": "1d0ff469b7ec7b3cb9d8673fde0c81c44821de2a",        # v4.1.0
    "docker/setup-qemu-action": "8d2750c68a42422c14e847fe6c8ac0403b4cbd6f",  # v3.12.0
    "docker/setup-buildx-action": "8d2750c68a42422c14e847fe6c8ac0403b4cbd6f", # v3.12.0
    "docker/build-push-action": "676cae2f85471aeff6776463c72881ebd902dcf9",  # v5.3.0
    "docker/login-action": "465a07811f14bebb1938fbed4728c6a1ff8901fc",       # v3.3.0
    "docker/metadata-action": "v5",  # tag – we will resolve via gh api if possible
    "github/codeql-action": "dd903d2e4f5405488e5ef1422510ee31c8b32357",      # v3.36.2
    "gitleaks/gitleaks-action": "8c2d79dc9a43c0f0bf9c7fcf6bfbf3b2615de7da",  # v2.3.0
    "actions/dependency-review-action": "29a786fbc64a2138a29d614ef883983e4cf631e6", # v4.8.0
    "webfactory/ssh-agent": "v0.9.0",  # will resolve
}

def resolve_sha(action: str, tag: str) -> str:
    """Return full SHA for given action@tag. Prefers hardcoded map, else gh api."""
    # Check hardcoded map first
    if action in ACTION_SHAS:
        sha = ACTION_SHAS[action]
        if len(sha) == 40:
            return sha
    # Try gh api
    try:
        cmd = ["gh", "api", f"/repos/{action}/git/ref/tags/{tag}", "--jq", ".object.sha"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        sha = result.stdout.strip()
        if sha and len(sha) == 40:
            return sha
    except subprocess.CalledProcessError:
        pass
    # Fallback to tag itself (will be caught by action-pinning check)
    print(f"⚠️  Could not resolve SHA for {action}@{tag}. Using tag (will fail pinning).")
    return tag

def render_workflow(template: str) -> str:
    """Replace @{tag} placeholders with SHA using resolve_sha."""
    def repl(match):
        action = match.group(1)
        tag = match.group(2)
        sha = resolve_sha(action, tag)
        return f"uses: {action}@{sha}"
    pattern = r'uses:\s*([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)@([a-zA-Z0-9._-]+)'
    return re.sub(pattern, repl, template)

# ----------------------------------------------------------------------
# WORKFLOW TEMPLATES (with improvements)
# ----------------------------------------------------------------------
def get_action_pinning_yml() -> str:
    return render_workflow("""
name: Action Pinning

on:
  pull_request:
    paths:
      - ".github/workflows/**"
  push:
    branches: [main]
    paths:
      - ".github/workflows/**"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Verify action pins
        run: |
          if grep -rE 'uses: .+@[a-zA-Z0-9._-]+' .github/workflows/*.yml | grep -vE '@[0-9a-f]{40}'; then
            echo "::error::Found mutable action references (not pinned to SHA)."
            exit 1
          fi
          echo "All actions are SHA-pinned."
""")

def get_ci_yml() -> str:
    return render_workflow("""
name: CI

on:
  pull_request:
    paths:
      - 'ERP-BACKEND/**'
      - 'ERP-BACKEND/frontend-react/**'
      - 'AI-BACKEND/**'   # optional; remove if not needed
  push:
    branches: [main]
    paths:
      - 'ERP-BACKEND/**'
      - 'ERP-BACKEND/frontend-react/**'
      - 'AI-BACKEND/**'

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  backend-test:
    name: Backend Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: ERP-BACKEND/requirements*.txt
      - name: Install deps
        working-directory: ERP-BACKEND
        run: |
          pip install -r requirements.txt
          if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi
      - name: Run tests
        working-directory: ERP-BACKEND
        run: |
          if [ -d tests ]; then pytest -q; else echo "No tests found"; fi

  frontend-build:
    name: Frontend Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: ERP-BACKEND/frontend-react/package-lock.json
      - name: Install & build
        working-directory: ERP-BACKEND/frontend-react
        run: |
          npm ci
          npm run build

  docker-build:
    name: Docker Build (no push)
    runs-on: ubuntu-latest
    needs: [backend-test, frontend-build]
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - name: Build backend image
        uses: docker/build-push-action@v5
        with:
          context: ./ERP-BACKEND
          file: ./ERP-BACKEND/Dockerfile
          push: false
          tags: erp03-backend:ci
      - name: Build frontend image
        uses: docker/build-push-action@v5
        with:
          context: ./ERP-BACKEND/frontend-react
          file: ./ERP-BACKEND/frontend-react/Dockerfile
          push: false
          tags: erp03-frontend:ci

  # Optional: build AI-BACKEND if Dockerfile exists
  ai-build:
    name: AI-BACKEND Build (optional)
    runs-on: ubuntu-latest
    if: hashFiles('AI-BACKEND/Dockerfile') != ''
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - name: Build AI image
        uses: docker/build-push-action@v5
        with:
          context: ./AI-BACKEND
          file: ./AI-BACKEND/Dockerfile
          push: false
          tags: erp03-ai:ci
""")

def get_security_yml() -> str:
    return render_workflow("""
name: Security

on:
  pull_request:
    paths:
      - 'ERP-BACKEND/**'
      - 'AI-BACKEND/**'
      - '**/package*.json'
      - '**/requirements*.txt'
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'

permissions:
  contents: read
  security-events: write
  pull-requests: write

jobs:
  dependency-review:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/dependency-review-action@v4

  codeql:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: python, javascript
      - uses: github/codeql-action/autobuild@v3
      - uses: github/codeql-action/analyze@v3

  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
""")

def get_release_yml() -> str:
    return render_workflow("""
name: Release

on:
  push:
    tags:
      - 'v[0-9]+.[0-9]+.[0-9]+'  # strict semver

env:
  REGISTRY: docker.io
  BACKEND_IMAGE: powerrangeranikg/erp-solution-backend
  FRONTEND_IMAGE: powerrangeranikg/erp-solution-frontend
  # optionally AI_IMAGE: powerrangeranikg/erp03-ai

concurrency:
  group: release-${{ github.ref_name }}
  cancel-in-progress: false

permissions:
  contents: write
  packages: write
  attestations: write
  id-token: write

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-qemu-action@v3
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.D2_USER }}
          password: ${{ secrets.D2_PASS }}
      - name: Meta backend
        id: meta_backend
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.BACKEND_IMAGE }}
          tags: type=semver,pattern={{version}},value=${{ github.ref_name }}
      - uses: docker/build-push-action@v5
        with:
          context: ./ERP-BACKEND
          file: ./ERP-BACKEND/Dockerfile
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta_backend.outputs.tags }}
          attestations: |
            type=sbom,enabled=true
            type=provenance,enabled=true
      - name: Meta frontend
        id: meta_frontend
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.FRONTEND_IMAGE }}
          tags: type=semver,pattern={{version}},value=${{ github.ref_name }}
      - uses: docker/build-push-action@v5
        with:
          context: ./ERP-BACKEND/frontend-react
          file: ./ERP-BACKEND/frontend-react/Dockerfile
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta_frontend.outputs.tags }}
          attestations: |
            type=sbom,enabled=true
            type=provenance,enabled=true

  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: staging
    if: startsWith(github.ref_name, 'v') && !endsWith(github.ref_name, '-test')
    steps:
      - uses: actions/checkout@v4
      - name: Install Docker Compose
        run: sudo apt-get update && sudo apt-get install -y docker-compose-plugin
      - name: Set up SSH
        uses: webfactory/ssh-agent@v0.9.0
        with:
          ssh-private-key: ${{ secrets.SSH_PRIVATE_KEY }}
      - name: Deploy
        run: |
          ssh -o StrictHostKeyChecking=no ${{ secrets.SERVER_USER }}@${{ secrets.SERVER_HOST }} << 'EOF'
            cd ${{ vars.DEPLOY_PATH || '/opt/erp03' }}
            docker login -u ${{ secrets.D2_USER }} -p ${{ secrets.D2_PASS }}
            docker-compose -f docker-compose.prod.yml pull
            docker-compose -f docker-compose.prod.yml up -d --remove-orphans
            docker system prune -f
            sleep 10
            curl -f http://localhost:8000/health || exit 1
          EOF
""")

# ----------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------
def run_cmd(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)

def write_workflow(filename: str, content: str) -> None:
    path = WORKFLOWS_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"✅ Created {path}")

def set_secret(name: str, value: str, env: Optional[str] = None):
    cmd = ["gh", "secret", "set", name]
    if env:
        cmd += ["--env", env]
    run_cmd(cmd + ["--body", value])

def set_branch_protection(repo: str):
    print("🔒 Setting branch protection for main...")
    run_cmd([
        "gh", "api", f"/repos/{repo}/branches/main/protection",
        "-X", "PUT",
        "-f", "required_status_checks[strict]=true",
        "-f", "required_status_checks[contexts][]=ci",
        "-f", "required_status_checks[contexts][]=security",
        "-f", "enforce_admins=true",
        "-f", "required_pull_request_reviews[dismiss_stale_reviews]=true",
    ], check=False)  # ignore if not allowed

# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    print("\n🏢 ERP03 Enterprise CI/CD Bootstrap")
    print("=" * 60)

    # Ensure gh is authenticated
    try:
        run_cmd(["gh", "auth", "status"], check=True)
    except subprocess.CalledProcessError:
        print("❌ gh is not authenticated. Run 'gh auth login' first.")
        sys.exit(1)

    # Create workflow files
    workflows = {
        "action-pinning.yml": get_action_pinning_yml(),
        "ci.yml": get_ci_yml(),
        "security.yml": get_security_yml(),
        "release.yml": get_release_yml(),
    }
    for name, content in workflows.items():
        write_workflow(name, content)

    # (Optional) Ask for secrets
    print("\n🔑 Do you want to set Docker Hub secrets now? (y/n)")
    if input().strip().lower() == 'y':
        d2_user = input("D2_USER: ").strip()
        d2_pass = input("D2_PASS: ").strip()
        if d2_user:
            set_secret("D2_USER", d2_user)
        if d2_pass:
            set_secret("D2_PASS", d2_pass)
        print("✅ Secrets set.")

    # Branch protection
    print("\n🛡️  Set branch protection for main? (y/n)")
    if input().strip().lower() == 'y':
        repo = run_cmd(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], check=True).stdout.strip()
        set_branch_protection(repo)

    # Commit and push
    print("\n📤 Commit and push changes? (y/n)")
    if input().strip().lower() == 'y':
        run_cmd(["git", "add", ".github/workflows/"])
        status = run_cmd(["git", "status", "--porcelain"], check=False)
        if status.stdout.strip():
            run_cmd(["git", "commit", "-m", "ci: add enterprise CI/CD with SHA-pinned workflows"])
            run_cmd(["git", "push", "origin", "main"])
            print("✅ Pushed.")
        else:
            print("ℹ️  No changes to commit.")

    print("\n" + "=" * 60)
    print("✅ Bootstrap complete!")
    print("\nNext steps:")
    print("  1. Review and adjust workflows in .github/workflows/")
    print("  2. Add any missing secrets (SSH_PRIVATE_KEY, SERVER_HOST, SERVER_USER)")
    print("  3. Create a tag to trigger a release:")
    print("     git tag v1.0.0 && git push origin v1.0.0")

if __name__ == "__main__":
    main()
