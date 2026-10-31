#!/usr/bin/env bash
###############################################################################
# ERP SOLUTION — GitHub Repository Manager
# Usage: ./scripts/gh-manager.sh [command]
###############################################################################

set -e

REPO="nyeinpyaesone-ui/ERP"
BRANCH="main"

C='[0;36m'; G='[0;32m'; Y='[1;33m'; R='[0;31m'; NC='[0m'

info()  { echo -e "${C}[i]${NC} $1"; }
ok()    { echo -e "${G}[✓]${NC} $1"; }
warn()  { echo -e "${Y}[!]${NC} $1"; }
err()   { echo -e "${R}[✗]${NC} $1"; }

cmd_help() {
    echo "ERP SOLUTION GitHub Manager"
    echo ""
    echo "Commands:"
    echo "  status      Show repository status"
    echo "  sync        Pull latest changes from remote"
    echo "  push        Push local changes to remote"
    echo "  force       Force push (overwrite remote)"
    echo "  log         Show recent commit history"
    echo "  files       List all tracked files"
    echo "  size        Show repository size breakdown"
    echo "  clean       Remove untracked files"
    echo "  reset       Hard reset to last commit"
    echo "  branch      List all branches"
    echo "  tag         Create version tag (e.g., ./gh-manager.sh tag v1.0.0)"
    echo "  release     Push tag and trigger release workflow"
    echo "  verify      Full verification report"
    echo "  help        Show this help"
}

cmd_status() {
    info "Repository Status"
    echo "  Remote:  https://github.com/${REPO}"
    echo "  Branch:  $(git branch --show-current)"
    echo "  Commits: $(git rev-list --count HEAD)"
    echo "  Files:   $(git ls-files | wc -l)"
    echo ""
    git status -sb
}

cmd_sync() {
    info "Syncing with remote..."
    git fetch origin
    git pull origin ${BRANCH} --rebase
    ok "Synced"
}

cmd_push() {
    info "Pushing to remote..."
    git push -u origin ${BRANCH}
    ok "Pushed"
}

cmd_force() {
    warn "Force pushing will OVERWRITE remote history!"
    read -rp "Are you sure? [y/N]: " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        git push -u origin ${BRANCH} --force
        ok "Force pushed"
    else
        info "Aborted"
    fi
}

cmd_log() {
    info "Recent commits"
    git log --oneline --graph --decorate -15
}

cmd_files() {
    info "Tracked files"
    git ls-files | head -50
    total=$(git ls-files | wc -l)
    [ "$total" -gt 50 ] && echo "... and $((total - 50)) more files"
}

cmd_size() {
    info "Repository size breakdown"
    du -sh .git 2>/dev/null || true
    du -sh . 2>/dev/null || true
    echo ""
    echo "Top 10 largest files:"
    git ls-files | xargs -I {} sh -c 'du -h "{}" 2>/dev/null' | sort -rh | head -10
}

cmd_clean() {
    warn "This will remove all untracked files!"
    git status --short
    read -rp "Proceed? [y/N]: " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        git clean -fd
        ok "Cleaned"
    fi
}

cmd_reset() {
    warn "This will discard all uncommitted changes!"
    read -rp "Proceed? [y/N]: " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        git reset --hard HEAD
        ok "Reset to HEAD"
    fi
}

cmd_branch() {
    info "Branches"
    git branch -a
}

cmd_tag() {
    version="${1:-v1.0.0}"
    info "Creating tag ${version}..."
    git tag -a "${version}" -m "Release ${version}"
    git push origin "${version}"
    ok "Tag ${version} created and pushed"
    info "This triggers the release workflow at .github/workflows/release.yml"
}

cmd_release() {
    info "Available tags:"
    git tag -l
    read -rp "Enter version to release (e.g., v1.0.0): " version
    [ -z "$version" ] && { err "No version specified"; exit 1; }
    cmd_tag "$version"
}

cmd_verify() {
    info "Full Verification Report"
    echo "=========================================="
    echo "Repository: ${REPO}"
    echo "Branch:     ${BRANCH}"
    echo "Commits:    $(git rev-list --count HEAD)"
    echo "Files:      $(git ls-files | wc -l)"
    echo "Remote:     $(git remote get-url origin)"
    echo ""
    echo "File breakdown:"
    git ls-files | sed 's|/.*||' | sort | uniq -c | sort -rn
    echo ""
    echo "Latest commit:"
    git log -1 --oneline
    echo "=========================================="
}

# Main
case "${1:-help}" in
    status)   cmd_status ;;
    sync)     cmd_sync ;;
    push)     cmd_push ;;
    force)    cmd_force ;;
    log)      cmd_log ;;
    files)    cmd_files ;;
    size)     cmd_size ;;
    clean)    cmd_clean ;;
    reset)    cmd_reset ;;
    branch)   cmd_branch ;;
    tag)      cmd_tag "$2" ;;
    release)  cmd_release ;;
    verify)   cmd_verify ;;
    help|*)   cmd_help ;;
esac
