#!/bin/bash

# Script to pull all changes from all branches in all GitHub repositories
# Usage: ./pull_all_repos.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default directory for GitHub repos
GITHUB_DIR="${GITHUB_DIR:-$HOME/Documents/GitHub}"

# Check if the GitHub directory exists
if [ ! -d "$GITHUB_DIR" ]; then
    echo -e "${RED}Error: GitHub directory not found at $GITHUB_DIR${NC}"
    echo "Set GITHUB_DIR environment variable or create the directory"
    exit 1
fi

# Change to GitHub directory
cd "$GITHUB_DIR" || exit 1

echo -e "${BLUE}=== Pulling all changes from GitHub repositories ===${NC}"
echo -e "Working directory: $GITHUB_DIR\n"

# Track statistics
total_repos=0
successful_pulls=0
failed_pulls=0
repos_with_changes=0

# Process each directory
for repo in */; do
    if [ -d "$repo/.git" ]; then
        ((total_repos++))
        echo -e "${GREEN}Processing repository: ${repo%/}${NC}"
        cd "$repo" || continue
        
        # Fetch all remotes and prune deleted branches
        echo "  Fetching all remotes and pruning deleted branches..."
        git fetch --all --prune
        
        # Get current branch
        current_branch=$(git branch --show-current)
        echo "  Current branch: $current_branch"
        
        # Clean up stale remote-tracking references
        git remote prune origin 2>/dev/null
        
        # Get list of all local branches
        branches=$(git branch --format='%(refname:short)')
        
        # Track if any branch had changes
        repo_had_changes=false
        stale_branches=()
        
        # Pull changes for each branch
        for branch in $branches; do
            echo -e "  ${YELLOW}Checking branch: $branch${NC}"
            
            # Switch to the branch
            git checkout "$branch" --quiet 2>/dev/null
            
            if [ $? -eq 0 ]; then
                # Get the remote tracking branch
                remote_branch=$(git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>/dev/null)
                
                if [ -n "$remote_branch" ]; then
                    # Check if the remote branch still exists
                    if git show-ref --verify --quiet "refs/remotes/$remote_branch"; then
                        # Check if there are updates
                        LOCAL=$(git rev-parse @)
                        REMOTE=$(git rev-parse "@{u}" 2>/dev/null)
                        BASE=$(git merge-base @ "@{u}" 2>/dev/null)
                        
                        if [ "$LOCAL" = "$REMOTE" ]; then
                            echo "    Already up to date"
                        elif [ "$LOCAL" = "$BASE" ]; then
                            echo "    Pulling changes..."
                            if git pull --ff-only; then
                                echo -e "    ${GREEN}✓ Successfully pulled changes${NC}"
                                repo_had_changes=true
                            else
                                echo -e "    ${RED}✗ Failed to pull (might need merge)${NC}"
                                ((failed_pulls++))
                            fi
                        elif [ "$REMOTE" = "$BASE" ]; then
                            echo -e "    ${YELLOW}Local branch is ahead of remote${NC}"
                        else
                            echo -e "    ${RED}Branches have diverged, manual merge required${NC}"
                            ((failed_pulls++))
                        fi
                    else
                        echo -e "    ${RED}Remote branch no longer exists (stale)${NC}"
                        if [ "$branch" != "$current_branch" ]; then
                            stale_branches+=("$branch")
                        fi
                    fi
                else
                    echo "    No remote tracking branch (local only)"
                fi
            else
                echo -e "    ${RED}Failed to checkout branch${NC}"
            fi
        done
        
        # Handle stale branches
        if [ ${#stale_branches[@]} -gt 0 ]; then
            echo -e "  ${YELLOW}Found ${#stale_branches[@]} stale branch(es) with deleted remotes${NC}"
            for stale_branch in "${stale_branches[@]}"; do
                echo -e "    ${RED}Stale: $stale_branch${NC}"
            done
        fi
        
        # Return to original branch
        git checkout "$current_branch" --quiet 2>/dev/null
        
        if [ "$repo_had_changes" = true ]; then
            ((repos_with_changes++))
        fi
        
        ((successful_pulls++))
        cd ..
        echo ""
    else
        echo -e "${YELLOW}Skipping ${repo%/}: Not a git repository${NC}\n"
    fi
done

# Summary
echo -e "${BLUE}=== Summary ===${NC}"
echo "Total repositories processed: $total_repos"
echo "Repositories with updates: $repos_with_changes"
echo "Successful repository pulls: $successful_pulls"
echo "Failed pulls (manual intervention needed): $failed_pulls"

# Check for uncommitted changes
echo -e "\n${BLUE}=== Checking for uncommitted changes ===${NC}"
repos_with_uncommitted=0

for repo in */; do
    if [ -d "$repo/.git" ]; then
        cd "$repo" || continue
        
        # Check for uncommitted changes
        if ! git diff-index --quiet HEAD -- 2>/dev/null; then
            echo -e "${YELLOW}${repo%/} has uncommitted changes${NC}"
            ((repos_with_uncommitted++))
        fi
        
        # Check for untracked files
        if [ -n "$(git ls-files --others --exclude-standard)" ]; then
            echo -e "${YELLOW}${repo%/} has untracked files${NC}"
        fi
        
        cd ..
    fi
done

if [ $repos_with_uncommitted -eq 0 ]; then
    echo -e "${GREEN}All repositories are clean${NC}"
fi

echo -e "\n${GREEN}Done!${NC}"
