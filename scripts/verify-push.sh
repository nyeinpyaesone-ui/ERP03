#!/bin/bash
echo "=== ERP SOLUTION Verification ==="
echo "Repository: https://github.com/nyeinpyaesone-ui/ERP"
echo "Branch: $(git branch --show-current)"
echo "Commits: $(git rev-list --count HEAD)"
echo "Files: $(git ls-files | wc -l)"
echo "Latest: $(git log -1 --oneline)"
echo ""
echo "Top-level directories:"
git ls-tree -d --name-only HEAD | sort
echo ""
echo "File count by directory:"
git ls-files | sed 's|/.*||' | sort | uniq -c | sort -rn | head -20
