#!/bin/bash

# Function to list branches and select one for commit
interactive_commit() {
    echo "=== Available Branches ==="
    
    # Clean up stale remote branches
    echo "Cleaning up deleted remote branches..."
    git remote prune origin 2>/dev/null
    
    # Get existing remote branches from remote
    remote_branches=()
    while IFS= read -r sha ref; do
        if [[ "$ref" == refs/heads/* ]]; then
            branch_name="${ref#refs/heads/}"
            remote_branches[${#remote_branches[@]}]="remotes/origin/$branch_name"
        fi
    done < <(git ls-remote --heads origin 2>/dev/null)
    
    # Get local branches that are not "gone" (deleted on remote)
    branches=()
    i=0
    
    # Filter local branches - only include those that still have remotes or are untracked
    while IFS= read -r line; do
        branch_name=$(echo "$line" | awk '{print $1}')
        # Skip branches marked as "gone"
        if echo "$line" | grep -q "gone]"; then
            echo "Skipping deleted branch: $branch_name"
            continue
        fi
        branches[i]="$branch_name"
        ((i++))
    done < <(git branch -vv | sed 's/^[* ] //')
    
    # Add remote branches that don't have local counterparts
    for remote_branch in "${remote_branches[@]}"; do
        branch_name="${remote_branch#remotes/origin/}"
        # Check if local branch exists
        local_exists=false
        for existing_branch in "${branches[@]}"; do
            if [[ "$existing_branch" == "$branch_name" ]]; then
                local_exists=true
                break
            fi
        done
        if [[ "$local_exists" == false ]]; then
            branches[i]="$remote_branch"
            ((i++))
        fi
    done
    
    # Display branches with numbers
    for i in "${!branches[@]}"; do
        current=""
        if git branch --show-current | grep -q "^${branches[i]#remotes/origin/}$"; then
            current=" (current)"
        fi
        echo "$((i+1)). ${branches[i]}$current"
    done
    
    echo ""
    echo -n "Select branch number (or 'q' to quit): "
    read -r choice
    
    # Handle quit
    if [[ "$choice" == "q" || "$choice" == "Q" ]]; then
        echo "Cancelled."
        return 1
    fi
    
    # Validate choice
    if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt "${#branches[@]}" ]; then
        echo "Invalid selection."
        return 1
    fi
    
    # Get selected branch
    selected_branch="${branches[$((choice-1))]}"
    
    # Handle remote branches (remove remotes/origin/ prefix)
    if [[ "$selected_branch" == remotes/origin/* ]]; then
        local_branch="${selected_branch#remotes/origin/}"
        # Check if local branch exists
        if git show-ref --verify --quiet "refs/heads/$local_branch"; then
            selected_branch="$local_branch"
        else
            echo "Creating local branch '$local_branch' from '$selected_branch'"
            git checkout -b "$local_branch" "$selected_branch"
            selected_branch="$local_branch"
        fi
    fi
    
    # Switch to branch if not already on it
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "$selected_branch" ]; then
        echo "Switching to branch: $selected_branch"
        git checkout "$selected_branch"
    else
        echo "Already on branch: $selected_branch"
    fi
    
    # Check for changes (including untracked files)
    if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
        echo "No changes to commit."
        return 0
    fi
    
    # Show status
    echo ""
    echo "=== Git Status ==="
    git status --short
    echo ""
    
    # Ask what to commit
    echo "What would you like to commit?"
    echo "1. Stage all changes and commit"
    echo "2. Commit only staged changes"
    echo "3. Select files to stage and commit"
    echo "4. Cancel"
    echo -n "Choice: "
    read -r commit_choice
    
    case $commit_choice in
        1)
            git add .
            ;;
        2)
            if git diff --cached --quiet; then
                echo "No staged changes found."
                return 1
            fi
            ;;
        3)
            echo "Current unstaged and untracked files:"
            git diff --name-only
            git ls-files --others --exclude-standard
            echo -n "Enter file patterns to stage (space-separated): "
            read -r files
            git add $files
            ;;
        4)
            echo "Cancelled."
            return 1
            ;;
        *)
            echo "Invalid choice."
            return 1
            ;;
    esac
    
    # Generate commit message
    echo ""
    echo "Generating commit message..."
    COMMIT_MSG=$(git diff --cached | claude -p "Write only a git commit message for these changes. Use conventional commit format. Return ONLY the commit message, no explanations or extra text. The summary line should be under 150 characters, but you can include a detailed body if needed for complex changes. Separate the summary from body with a blank line." --model claude-sonnet-4-20250514)
    
    echo ""
    echo "=== Generated Commit Message ==="
    echo "\"$COMMIT_MSG\""
    echo "================================="
    echo -n "Commit with this message? (y/n/e to edit): "
    read -r response
    
    case $response in
        [Yy]*)
            git commit -m "$COMMIT_MSG"
            echo "✅ Committed successfully to branch: $selected_branch"
            
            # Ask if user wants to push
            echo -n "Push to remote? (y/n): "
            read -r push_response
            if [[ "$push_response" =~ ^[Yy]$ ]]; then
                git push origin "$selected_branch"
                echo "✅ Pushed to origin/$selected_branch"
            fi
            ;;
        [Ee]*)
            echo -n "Enter your commit message: "
            read -r CUSTOM_MSG
            git commit -m "$CUSTOM_MSG"
            echo "✅ Committed successfully to branch: $selected_branch"
            
            # Ask if user wants to push
            echo -n "Push to remote? (y/n): "
            read -r push_response
            if [[ "$push_response" =~ ^[Yy]$ ]]; then
                git push origin "$selected_branch"
                echo "✅ Pushed to origin/$selected_branch"
            fi
            ;;
        *)
            echo "❌ Commit cancelled."
            ;;
    esac
}

# Make it available as a command
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    interactive_commit
fi
