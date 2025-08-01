#!/usr/bin/env python3
"""
Collect all GitHub issues and project data and save to disk.
This prevents hitting rate limits when running multiple analysis scripts.
"""
import json
import subprocess
import sys
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

# Configuration
DATA_DIR = Path(__file__).parent / "data"
ORG_NAME = "MaxMillerLab"
REPOS = [
    "MaxMillerLab/finance_and_dev",
    "MaxMillerLab/bills",
    "MaxMillerLab/referee",
    "MaxMillerLab/health", 
    "MaxMillerLab/foreign_influence",
    "MaxMillerLab/fara",
    "MaxMillerLab/democracy",
    "MaxMillerLab/reports",
    "MaxMillerLab/colonialism",
    "MaxMillerLab/inventory",
    "MaxMillerLab/ssw",
    "MaxMillerLab/propaganda",
    "MaxMillerLab/interest_rate_risk",
    "MaxMillerLab/discussions",
    "MaxMillerLab/ownership_chains",
    "MaxMillerLab/census",
    "MaxMillerLab/maxmiller.github.io",
    "MaxMillerLab/lab_manual",
    "MaxMillerLab/peps"
]


def run_gh_command(cmd):
    """Run a GitHub CLI command and return parsed JSON output"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from command {' '.join(cmd)}: {e}", file=sys.stderr)
        return None


def collect_issues_for_repo(repo_name):
    """Get all open issues for a repository with full metadata"""
    print(f"  Collecting issues for {repo_name}...", file=sys.stderr)
    
    # Get comprehensive issue data
    cmd = [
        "gh", "issue", "list", 
        "--repo", repo_name,
        "--state", "open",
        "--json", "number,title,url,updatedAt,createdAt,assignees,labels,milestone,projectItems,body,comments",
        "--limit", "1000"  # High limit to get all issues
    ]
    
    issues = run_gh_command(cmd)
    if issues is None:
        return []
    
    print(f"    Found {len(issues)} open issues", file=sys.stderr)
    return issues


def collect_projects_for_org(org_name):
    """Get all projects for an organization"""
    print(f"  Collecting projects for {org_name}...", file=sys.stderr)
    
    cmd = ["gh", "project", "list", "--owner", org_name, "--format", "json", "--limit", "1000"]
    
    data = run_gh_command(cmd)
    if data is None:
        return []
    
    projects = data.get('projects', [])
    print(f"    Found {len(projects)} projects", file=sys.stderr)
    return projects


def collect_project_items(project_number, org_name):
    """Get all items from a project with full metadata"""
    print(f"    Collecting items for project {project_number}...", file=sys.stderr)
    
    cmd = ["gh", "project", "item-list", str(project_number), "--owner", org_name, "--format", "json", "--limit", "1000"]
    
    data = run_gh_command(cmd)
    if data is None:
        return []
    
    items = data.get('items', [])
    print(f"      Found {len(items)} items", file=sys.stderr)
    return items


def collect_all_data():
    """Collect all GitHub data and save to files"""
    print(f"Starting data collection at {datetime.now().isoformat()}", file=sys.stderr)
    
    # Clear and recreate data directory
    if DATA_DIR.exists():
        print(f"Clearing existing data directory: {DATA_DIR}", file=sys.stderr)
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(exist_ok=True)
    
    # Collect timestamp
    collection_time = datetime.now(timezone.utc).isoformat()
    
    # Collect all issues
    print("\nCollecting issues from all repositories...", file=sys.stderr)
    all_issues = {}
    for repo in REPOS:
        issues = collect_issues_for_repo(repo)
        if issues:
            all_issues[repo] = issues
    
    # Save issues data
    issues_file = DATA_DIR / "issues.json"
    with open(issues_file, 'w') as f:
        json.dump({
            'collection_time': collection_time,
            'repositories': all_issues
        }, f, indent=2)
    print(f"\nSaved issues data to {issues_file}", file=sys.stderr)
    
    # Collect project data
    print(f"\nCollecting projects for {ORG_NAME}...", file=sys.stderr)
    projects = collect_projects_for_org(ORG_NAME)
    
    # Collect project items for each project
    project_items = {}
    for project in projects:
        project_number = project.get('number')
        project_title = project.get('title', 'Unknown')
        print(f"  Processing project {project_number}: {project_title}", file=sys.stderr)
        
        items = collect_project_items(project_number, ORG_NAME)
        if items:
            project_items[str(project_number)] = {
                'title': project_title,
                'items': items
            }
    
    # Save project data
    projects_file = DATA_DIR / "projects.json"
    with open(projects_file, 'w') as f:
        json.dump({
            'collection_time': collection_time,
            'organization': ORG_NAME,
            'projects': projects,
            'project_items': project_items
        }, f, indent=2)
    print(f"\nSaved project data to {projects_file}", file=sys.stderr)
    
    # Create a summary file
    summary = {
        'collection_time': collection_time,
        'total_repositories': len(all_issues),
        'total_issues': sum(len(issues) for issues in all_issues.values()),
        'total_projects': len(projects),
        'total_project_items': sum(len(data['items']) for data in project_items.values())
    }
    
    summary_file = DATA_DIR / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nData collection complete!", file=sys.stderr)
    print(f"Summary: {json.dumps(summary, indent=2)}", file=sys.stderr)
    

def main():
    """Main entry point"""
    collect_all_data()
    

if __name__ == "__main__":
    main()
