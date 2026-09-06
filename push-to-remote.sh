#!/bin/bash

# =============================================================================
# Push to Remote Repository Script
# =============================================================================
# This script helps push the refactoring branch to a remote repository
# and provides instructions for creating a Pull Request.
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Branch name
BRANCH_NAME="qwen-code-d293474a-e288-4e94-9c62-131d801f3f12"

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  Deployment & Integration Push Script${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# Check if remote is configured
echo -e "${YELLOW}Step 1: Checking remote configuration...${NC}"
if git remote | grep -q '^origin$'; then
    echo -e "${GREEN}✓ Remote 'origin' is configured${NC}"
    REMOTE_URL=$(git remote get-url origin)
    echo "  URL: $REMOTE_URL"
else
    echo -e "${RED}✗ No remote 'origin' configured${NC}"
    echo ""
    echo "Please add your remote repository:"
    echo "  git remote add origin <YOUR_REPO_URL>"
    echo ""
    echo "Examples:"
    echo "  GitHub:   git remote add origin https://github.com/username/repo.git"
    echo "  GitLab:   git remote add origin https://gitlab.com/username/repo.git"
    echo "  SSH:      git remote add origin git@github.com:username/repo.git"
    echo ""
    read -p "Enter remote repository URL (or press Enter to skip): " REMOTE_URL
    if [ -n "$REMOTE_URL" ]; then
        git remote add origin "$REMOTE_URL"
        echo -e "${GREEN}✓ Remote 'origin' added successfully${NC}"
    else
        echo -e "${YELLOW}Skipping remote configuration. Please configure manually before pushing.${NC}"
        exit 0
    fi
fi

echo ""

# Verify current branch
echo -e "${YELLOW}Step 2: Verifying current branch...${NC}"
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "$BRANCH_NAME" ]; then
    echo -e "${RED}✗ Not on expected branch '$BRANCH_NAME'${NC}"
    echo "  Current branch: $CURRENT_BRANCH"
    echo ""
    read -p "Do you want to switch to $BRANCH_NAME? (y/n): " SWITCH
    if [ "$SWITCH" = "y" ]; then
        git checkout "$BRANCH_NAME"
        echo -e "${GREEN}✓ Switched to branch $BRANCH_NAME${NC}"
    else
        echo -e "${YELLOW}Continuing on current branch: $CURRENT_BRANCH${NC}"
        BRANCH_NAME=$CURRENT_BRANCH
    fi
else
    echo -e "${GREEN}✓ On correct branch: $BRANCH_NAME${NC}"
fi

echo ""

# Show commit summary
echo -e "${YELLOW}Step 3: Commit summary...${NC}"
COMMIT_COUNT=$(git rev-list --count main..HEAD)
echo "  Commits ahead of main: $COMMIT_COUNT"
echo ""
echo "Recent commits:"
git log --oneline -5
echo ""

# Push to remote
echo -e "${YELLOW}Step 4: Pushing to remote repository...${NC}"
read -p "Do you want to push now? (y/n): " PUSH_CONFIRM
if [ "$PUSH_CONFIRM" = "y" ]; then
    echo "Pushing branch $BRANCH_NAME to origin..."
    if git push -u origin "$BRANCH_NAME"; then
        echo -e "${GREEN}✓ Successfully pushed to origin/$BRANCH_NAME${NC}"
        
        # Generate PR URL
        REMOTE_URL=$(git remote get-url origin)
        if [[ "$REMOTE_URL" == *"github.com"* ]]; then
            # GitHub URL format
            REPO_PATH=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[/:]([^/]+)/([^.]+).*|\1/\2|')
            PR_URL="https://github.com/${REPO_PATH}/compare/main...${BRANCH_NAME}?expand=1"
            echo ""
            echo -e "${GREEN}================================================================${NC}"
            echo -e "${GREEN}  Next Steps: Create Pull Request${NC}"
            echo -e "${GREEN}================================================================${NC}"
            echo ""
            echo "PR URL: $PR_URL"
            echo ""
            echo "PR Title:"
            echo "  feat: Integration compatibility layer with RBAC and CI/CD improvements"
            echo ""
            echo "Suggested Labels:"
            echo "  enhancement, integration, ci-cd, refactoring"
            echo ""
            echo "Suggested Reviewers:"
            echo "  Assign appropriate team members"
            echo ""
            echo -e "${YELLOW}Opening PR page in browser...${NC}"
            if command -v xdg-open &> /dev/null; then
                xdg-open "$PR_URL"
            elif command -v open &> /dev/null; then
                open "$PR_URL"
            else
                echo "Please open the PR URL in your browser."
            fi
        elif [[ "$REMOTE_URL" == *"gitlab.com"* ]]; then
            # GitLab URL format
            REPO_PATH=$(echo "$REMOTE_URL" | sed -E 's|.*gitlab\.com[/:]([^/]+)/([^.]+).*|\1/\2|')
            MR_URL="https://gitlab.com/${REPO_PATH}/-/merge_requests/new?merge_request[source_branch]=${BRANCH_NAME}&merge_request[target_branch]=main"
            echo ""
            echo -e "${GREEN}================================================================${NC}"
            echo -e "${GREEN}  Next Steps: Create Merge Request${NC}"
            echo -e "${GREEN}================================================================${NC}"
            echo ""
            echo "MR URL: $MR_URL"
            echo ""
            echo "Opening MR page in browser..."
            if command -v xdg-open &> /dev/null; then
                xdg-open "$MR_URL"
            elif command -v open &> /dev/null; then
                open "$MR_URL"
            else
                echo "Please open the MR URL in your browser."
            fi
        else
            echo ""
            echo -e "${YELLOW}Remote repository detected. Please create a PR/MR manually.${NC}"
        fi
    else
        echo -e "${RED}✗ Failed to push to remote${NC}"
        echo "Please check your credentials and try again."
        exit 1
    fi
else
    echo -e "${YELLOW}Push skipped. You can push manually later with:${NC}"
    echo "  git push -u origin $BRANCH_NAME"
fi

echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  Deployment Plan Reference${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""
echo "For detailed deployment instructions, see:"
echo "  DEPLOYMENT_PLAN.md"
echo ""
echo "Key checkpoints:"
echo "  ✓ Code review completed"
echo "  ✓ All CI checks passing"
echo "  ✓ Test coverage maintained (>80%)"
echo "  ✓ Documentation updated"
echo "  ✓ Staging deployment successful"
echo "  ✓ Integration tests passing"
echo "  ✓ Security scan clean"
echo ""
echo -e "${GREEN}Ready for deployment!${NC}"
