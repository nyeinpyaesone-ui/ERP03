#!/usr/bin/env bash
###############################################################################
# ERP SOLUTION — Project Statistics Generator
# Usage: ./scripts/project-stats.sh
###############################################################################

set -e

echo "=========================================="
echo "  ERP SOLUTION — Project Statistics"
echo "=========================================="
echo ""

# Git stats
echo "Git Statistics:"
echo "  Commits:        $(git rev-list --count HEAD)"
echo "  Contributors:   $(git log --format='%an' | sort -u | wc -l)"
echo "  Branches:       $(git branch -a | wc -l)"
echo "  Tags:           $(git tag -l | wc -l)"
echo ""

# File stats
echo "File Statistics:"
echo "  Total files:    $(git ls-files | wc -l)"
echo "  Total lines:    $(git ls-files | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')"
echo ""

# Language breakdown
echo "Language Breakdown:"
git ls-files | grep -E '\.(py|ts|tsx|js|jsx|yaml|yml|json|md|html|css|sh)$' | sed 's/.*\.//' | sort | uniq -c | sort -rn | while read count ext; do
    printf "  %-10s %4d files\n" "${ext}:" "$count"
done
echo ""

# Directory sizes
echo "Directory Sizes:"
du -sh backend frontend mobile infra docs scripts .github 2>/dev/null | sort -rh | while read size dir; do
    printf "  %-20s %s\n" "${dir}:" "$size"
done
echo ""

# Recent activity
echo "Recent Activity (last 7 days):"
git log --since="7 days ago" --oneline --no-walk --all 2>/dev/null | wc -l | xargs -I {} echo "  Commits: {}"
echo ""

echo "=========================================="
