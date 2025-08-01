#!/usr/bin/env python3
import json
import sys
import csv
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path

def load_cached_data():
    """Load cached GitHub data from files"""
    data_dir = Path(__file__).parent / "data"
    
    # Load issues data
    issues_file = data_dir / "issues.json"
    if not issues_file.exists():
        print(f"Error: Cached data not found at {issues_file}", file=sys.stderr)
        print("Please run collect_github_data.py first", file=sys.stderr)
        sys.exit(1)
    
    with open(issues_file, 'r') as f:
        issues_data = json.load(f)
    
    # Load projects data
    projects_file = data_dir / "projects.json"
    if not projects_file.exists():
        print(f"Error: Cached data not found at {projects_file}", file=sys.stderr)
        print("Please run collect_github_data.py first", file=sys.stderr)
        sys.exit(1)
    
    with open(projects_file, 'r') as f:
        projects_data = json.load(f)
    
    return issues_data, projects_data


def get_issues_for_repo(repo_name, issues_data):
    """Get all open issues for a repository from cached data"""
    return issues_data.get('repositories', {}).get(repo_name, [])

def calculate_days_since_update(updated_at):
    """Calculate days since last update"""
    updated_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
    current_date = datetime.now(timezone.utc)
    diff = current_date - updated_date
    return diff.days

def get_projects_for_org(org_name, projects_data):
    """Get all projects for an organization from cached data"""
    return projects_data.get('projects', [])


def get_project_items(project_number, org_name, projects_data):
    """Get all items from a project from cached data"""
    project_items = projects_data.get('project_items', {})
    project_data = project_items.get(str(project_number), {})
    return project_data.get('items', [])

def build_issue_to_project_map(org_name, projects_data):
    """Build a mapping from issue URLs to project status"""
    issue_to_project = {}
    
    print(f"Building project mapping for {org_name}...", file=sys.stderr)
    projects = get_projects_for_org(org_name, projects_data)
    
    for project in projects:
        project_number = project.get('number')
        project_title = project.get('title', 'Unknown')
        
        items = get_project_items(project_number, org_name, projects_data)
        
        for item in items:
            if item.get('content', {}).get('type') == 'Issue':
                issue_url = item.get('content', {}).get('url')
                status = item.get('status', 'No Status')
                if issue_url:
                    issue_to_project[issue_url] = {
                        'status': status,
                        'project': project_title
                    }
    
    return issue_to_project

def main():
    # Load cached data
    print("Loading cached GitHub data...", file=sys.stderr)
    issues_data, projects_data = load_cached_data()
    
    # Show when data was collected
    collection_time = issues_data.get('collection_time', 'Unknown')
    print(f"Using data collected at: {collection_time}", file=sys.stderr)
    
    repos = [
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
    
    # Build mapping from issues to project status
    print("Building project status mapping...", file=sys.stderr)
    issue_to_project = build_issue_to_project_map("MaxMillerLab", projects_data)
    
    stale_issues = []
    paused_issues = []
    
    for repo in repos:
        print(f"Checking {repo}...", file=sys.stderr)
        issues = get_issues_for_repo(repo, issues_data)
        
        for issue in issues:
            days_inactive = calculate_days_since_update(issue['updatedAt'])
            
            # Get project status if available
            project_info = issue_to_project.get(issue['url'], {})
            project_status = project_info.get('status', 'Not in Project')
            project_name = project_info.get('project', 'N/A')
            
            issue_data = {
                'repo': repo,
                'number': issue['number'],
                'title': issue['title'],
                'url': issue['url'],
                'days_inactive': days_inactive,
                'updated_at': issue['updatedAt'],
                'project_status': project_status,
                'project_name': project_name,
                'assignees': [assignee['login'] for assignee in issue.get('assignees', [])]
            }
            
            # Track paused issues separately
            if project_status == 'Pause':
                paused_issues.append(issue_data)
            
            if days_inactive > 5:
                stale_issues.append(issue_data)
    
    # Sort by days inactive (most stale first)
    stale_issues.sort(key=lambda x: x['days_inactive'], reverse=True)
    paused_issues.sort(key=lambda x: x['days_inactive'], reverse=True)
    
    # Export to CSV
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    csv_file = output_dir / "stale_issues.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['repository', 'issue_number', 'title', 'assignees', 'days_inactive', 'last_updated', 'project_status', 'url'])
        writer.writeheader()
        
        for issue in stale_issues:
            writer.writerow({
                'repository': issue['repo'].split('/')[-1],
                'issue_number': issue['number'],
                'title': issue['title'],
                'assignees': ','.join(issue['assignees']) if issue['assignees'] else '',
                'days_inactive': issue['days_inactive'],
                'last_updated': issue['updated_at'][:10],
                'project_status': issue['project_status'],
                'url': issue['url']
            })
    
    print(f"CSV data saved to: {csv_file}", file=sys.stderr)
    
    # Print markdown report
    print("\n## Issues inactive for more than 5 days:\n")
    print("| Repository | Issue | Title | Assignees | Days Inactive | Last Updated | Project Status |")
    print("|------------|-------|-------|-----------|---------------|--------------|----------------|")
    
    for issue in stale_issues:
        repo_short = issue['repo'].split('/')[-1]
        status_display = issue['project_status']
        if issue['project_status'] == 'Pause':
            status_display = "🔶 **Pause**"
        elif issue['project_status'] == 'Not in Project':
            status_display = "⚪ No Project"
        
        # Format assignees
        assignees_str = ', '.join(issue['assignees']) if issue['assignees'] else 'Unassigned'
        
        print(f"| {repo_short} | [#{issue['number']}]({issue['url']}) | {issue['title']} | {assignees_str} | {issue['days_inactive']} | {issue['updated_at'][:10]} | {status_display} |")
    
    # Show summary of paused issues
    if paused_issues:
        print("\n## Summary of Paused Issues:\n")
        print("| Repository | Issue | Title | Assignees | Days Since Last Update |")
        print("|------------|-------|-------|-----------|------------------------|")
        
        for issue in paused_issues:
            repo_short = issue['repo'].split('/')[-1]
            assignees_str = ', '.join(issue['assignees']) if issue['assignees'] else 'Unassigned'
            print(f"| {repo_short} | [#{issue['number']}]({issue['url']}) | {issue['title']} | {assignees_str} | {issue['days_inactive']} |")
        
        print(f"\n**Total paused issues: {len(paused_issues)}**")

if __name__ == "__main__":
    main()
