#!/usr/bin/env python3
"""
Add issues from repositories to their associated GitHub projects.

This script identifies issues that are not yet added to projects and adds them
to the appropriate project based on repository-project mappings.

Usage:
    python3 add_issues_to_projects.py                    # Dry run - show what would be added
    python3 add_issues_to_projects.py --execute          # Actually add issues to projects
    python3 add_issues_to_projects.py --filter-repo bills  # Only process specific repository
"""

import json
import subprocess
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime

# Repository to Project mappings
# Based on analysis of existing project assignments
REPO_TO_PROJECT_MAPPING = {
    "census": "Census",
    "lab_manual": "Lab Manual Wiki",
    "propaganda": "Propaganda",
    "bills": "Bill Probability and Impact",
    "health": "Health",
    "inventory": "Inventory",
    "colonialism": "Colonial Hedge",
    "democracy": "Who values democracy?",
    "ssw": "Social Security and Inequality",
    "peps": "PEPs",
    "interest_rate_risk": "Social Security II",  # Corrected mapping
    "foreign_influence": "Foreign Influence",
    "finance_and_dev": "Emerging markets risk",  # Discovered from analysis
    # Add more mappings as needed
}

# Organization name
ORG_NAME = "MaxMillerLab"

class ProjectIssueManager:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.issues_data = None
        self.projects_data = None
        self.project_items = {}
        self.issues_to_add = []
        
    def load_data(self):
        """Load cached GitHub data from files."""
        data_dir = Path("data")
        
        # Load issues data
        issues_file = data_dir / "issues.json"
        if not issues_file.exists():
            print(f"Error: Cached data not found at {issues_file}")
            print("Please run collect_github_data.py first")
            sys.exit(1)
        
        with open(issues_file, 'r') as f:
            self.issues_data = json.load(f)
        
        # Load projects data
        projects_file = data_dir / "projects.json"
        if not projects_file.exists():
            print(f"Error: Cached data not found at {projects_file}")
            print("Please run collect_github_data.py first")
            sys.exit(1)
        
        with open(projects_file, 'r') as f:
            self.projects_data = json.load(f)
    
    def get_project_by_title(self, title: str) -> Optional[Dict]:
        """Find a project by its title."""
        for project in self.projects_data.get('projects', []):
            if project.get('title') == title:
                return project
        return None
    
    def get_issues_already_in_project(self, project_number: int) -> Set[str]:
        """Get all issue URLs that are already in a project."""
        issue_urls = set()
        
        project_items = self.projects_data.get('project_items', {}).get(str(project_number), {})
        items = project_items.get('items', [])
        
        for item in items:
            if item.get('content', {}).get('type') == 'Issue':
                issue_url = item.get('content', {}).get('url')
                if issue_url:
                    issue_urls.add(issue_url)
        
        return issue_urls
    
    def find_issues_not_in_projects(self, repo_filter=None):
        """Find all issues that need to be added to projects."""
        self.issues_to_add = []
        
        # Process each repository
        for repo_full_name, issues in self.issues_data.get('repositories', {}).items():
            repo_short_name = repo_full_name.split('/')[-1]
            
            # Apply repository filter if specified
            if repo_filter and repo_short_name != repo_filter:
                continue
            
            # Check if this repository has a mapped project
            if repo_short_name not in REPO_TO_PROJECT_MAPPING:
                print(f"Warning: No project mapping found for repository '{repo_short_name}'", file=sys.stderr)
                continue
            
            project_title = REPO_TO_PROJECT_MAPPING[repo_short_name]
            project = self.get_project_by_title(project_title)
            
            if not project:
                print(f"Warning: Project '{project_title}' not found for repository '{repo_short_name}'", file=sys.stderr)
                continue
            
            project_number = project.get('number')
            project_id = project.get('id')
            
            # Get issues already in the project
            issues_in_project = self.get_issues_already_in_project(project_number)
            
            # Check each issue in the repository
            for issue in issues:
                issue_url = issue.get('url')
                issue_number = issue.get('number')
                issue_title = issue.get('title')
                
                # Skip if already in project
                if issue_url in issues_in_project:
                    continue
                
                # Add to list of issues to add
                self.issues_to_add.append({
                    'repo': repo_short_name,
                    'issue_number': issue_number,
                    'issue_title': issue_title,
                    'issue_url': issue_url,
                    'project_title': project_title,
                    'project_number': project_number,
                    'project_id': project_id
                })
        
        # Sort by repository and issue number
        self.issues_to_add.sort(key=lambda x: (x['repo'], x['issue_number']))
    
    def add_issue_to_project(self, repo: str, issue_number: int, project_number: int):
        """Add an issue to a project using gh CLI."""
        if self.dry_run:
            return True  # Simulate success in dry run
        
        try:
            # Construct the issue URL
            issue_url = f"https://github.com/{ORG_NAME}/{repo}/issues/{issue_number}"
            
            # Add the issue to the project using URL
            cmd = [
                "gh", "project", "item-add", str(project_number),
                "--owner", ORG_NAME,
                "--url", issue_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Successfully added {repo}#{issue_number} to project")
                return True
            else:
                print(f"❌ Failed to add {repo}#{issue_number} to project: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error adding {repo}#{issue_number} to project: {str(e)}")
            return False
    
    def run(self, repo_filter=None):
        """Main execution method."""
        print("Loading GitHub data...")
        self.load_data()
        
        print(f"Data collection time: {self.issues_data.get('collection_time', 'Unknown')}")
        print()
        
        print("Finding issues not in projects...")
        self.find_issues_not_in_projects(repo_filter=repo_filter)
        
        if not self.issues_to_add:
            print("✨ All issues are already in their projects!")
            return
        
        print(f"\nFound {len(self.issues_to_add)} issues to add to projects:\n")
        
        # Group by project for better display
        by_project = {}
        for item in self.issues_to_add:
            project = item['project_title']
            if project not in by_project:
                by_project[project] = []
            by_project[project].append(item)
        
        # Display what will be done
        for project_title, items in sorted(by_project.items()):
            print(f"📋 **{project_title}** ({len(items)} issues)")
            for item in items:
                print(f"   - {item['repo']}#{item['issue_number']}: {item['issue_title']}")
            print()
        
        if self.dry_run:
            print("-" * 60)
            print("🔍 DRY RUN - No changes made")
            print("Run with --execute to actually add issues to projects")
        else:
            print("-" * 60)
            print("Adding issues to projects...")
            print()
            
            success_count = 0
            for item in self.issues_to_add:
                print(f"Adding {item['repo']}#{item['issue_number']} to {item['project_title']}...", end=" ")
                if self.add_issue_to_project(item['repo'], item['issue_number'], item['project_number']):
                    success_count += 1
            
            print()
            print("-" * 60)
            print(f"✅ Complete! Successfully added {success_count}/{len(self.issues_to_add)} issues to projects")


def main():
    parser = argparse.ArgumentParser(
        description="Add issues from repositories to their associated projects"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually add issues to projects (default is dry run)"
    )
    parser.add_argument(
        "--filter-repo",
        help="Only process issues from a specific repository"
    )
    
    args = parser.parse_args()
    
    # Check if gh CLI is available
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: GitHub CLI (gh) is not installed or not in PATH.")
        print("Please install it from: https://cli.github.com/")
        sys.exit(1)
    
    # Check if user is authenticated
    try:
        subprocess.run(["gh", "auth", "status"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("Error: Not authenticated with GitHub CLI.")
        print("Please run: gh auth login")
        sys.exit(1)
    
    manager = ProjectIssueManager(dry_run=not args.execute)
    
    # Apply repository filter if specified
    if args.filter_repo:
        print(f"Filtering to repository: {args.filter_repo}")
    
    manager.run(repo_filter=args.filter_repo)


if __name__ == "__main__":
    main()
