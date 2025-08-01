#!/usr/bin/env python3
import json
import sys
import csv
from collections import defaultdict
from datetime import datetime, timezone
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


def get_projects_for_org(org_name, projects_data):
    """Get all projects for an organization from cached data"""
    return projects_data.get('projects', [])


def get_project_items(project_number, org_name, projects_data):
    """Get all items from a project from cached data"""
    project_items = projects_data.get('project_items', {})
    project_data = project_items.get(str(project_number), {})
    return project_data.get('items', [])


def build_issue_project_metadata(org_name, projects_data):
    """Build a mapping from issue URLs to project metadata"""
    issue_metadata = {}
    
    print(f"Building project metadata for {org_name}...", file=sys.stderr)
    projects = get_projects_for_org(org_name, projects_data)
    
    for project in projects:
        project_number = project.get('number')
        project_title = project.get('title', 'Unknown')
        
        print(f"  Scanning project {project_number}: {project_title}...", file=sys.stderr)
        items = get_project_items(project_number, org_name, projects_data)
        
        for item in items:
            if item.get('content', {}).get('type') == 'Issue':
                issue_url = item.get('content', {}).get('url')
                if issue_url:
                    # Extract all available fields
                    fields = {}
                    for field_name, field_value in item.items():
                        if field_name not in ['id', 'content']:
                            fields[field_name] = field_value
                    
                    issue_metadata[issue_url] = {
                        'project': project_title,
                        'project_number': project_number,
                        'status': item.get('status', ''),
                        'priority': item.get('priority', ''),
                        'start_date': item.get('start date', ''),
                        'target_date': item.get('target completion date', ''),
                        'fields': fields
                    }
    
    return issue_metadata


def analyze_issue(issue, issue_metadata):
    """Analyze an issue and return reasons why it's flagged"""
    reasons = []
    url = issue['url']
    metadata = issue_metadata.get(url, {})
    
    # Check if assigned to a project
    if not metadata.get('project'):
        reasons.append("Not assigned to a project")
    else:
        # Check priority
        if not metadata.get('priority'):
            reasons.append("No priority set")
        
        # Check status
        if not metadata.get('status'):
            reasons.append("No status set")
    
    # Check assignees
    if not issue.get('assignees'):
        reasons.append("Not assigned to anyone")
    
    # Check dates (only if in a project)
    if metadata.get('project'):
        if not metadata.get('start_date'):
            reasons.append("No start date")
        if not metadata.get('target_date'):
            reasons.append("No target completion date")
    
    return reasons


def main():
    # Load cached data
    print("Loading cached GitHub data...", file=sys.stderr)
    issues_data, projects_data = load_cached_data()

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
    
    # Build metadata mapping for all issues across projects
    print("Building issue metadata from projects...", file=sys.stderr)
    issue_metadata = build_issue_project_metadata("MaxMillerLab", projects_data)
    print(f"Found metadata for {len(issue_metadata)} issues in projects\n", file=sys.stderr)
    
    flagged_issues = []
    total_issues = 0
    
    for repo in repos:
        print(f"Checking {repo}...", file=sys.stderr)
        issues = get_issues_for_repo(repo, issues_data)
        total_issues += len(issues)
        
        for issue in issues:
            reasons = analyze_issue(issue, issue_metadata)
            
            if reasons:
                flagged_issues.append({
                    'repo': repo,
                    'number': issue['number'],
                    'title': issue['title'],
                    'url': issue['url'],
                    'reasons': reasons,
                    'metadata': issue_metadata.get(issue['url'], {}),
                    'assignees': [assignee['login'] for assignee in issue.get('assignees', [])]
                })
    
    # Sort by number of reasons (most problematic first)
    flagged_issues.sort(key=lambda x: len(x['reasons']), reverse=True)
    
    # Export to CSV
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    csv_file = output_dir / "issues_without_info.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['repository', 'issue_number', 'title', 'assignees', 'reasons', 'url'])
        writer.writeheader()
        
        for issue in flagged_issues:
            writer.writerow({
                'repository': issue['repo'].split('/')[-1],
                'issue_number': issue['number'],
                'title': issue['title'],
                'assignees': ','.join(issue['assignees']) if issue['assignees'] else '',
                'reasons': '|'.join(issue['reasons']),  # Using | as separator since reasons may contain commas
                'url': issue['url']
            })
    
    print(f"CSV data saved to: {csv_file}", file=sys.stderr)
    
    # Print markdown report
    print(f"\n## Flagged Issues Report\n")
    print(f"**Total open issues scanned:** {total_issues}")
    print(f"**Issues with missing metadata:** {len(flagged_issues)}\n")
    
    if flagged_issues:
        print("| Repository | Issue | Title | Assignees | Reasons |")
        print("|------------|-------|-------|-----------|---------|")
        
        for issue in flagged_issues:
            repo_short = issue['repo'].split('/')[-1]
            reasons_str = '<br>• '.join(issue['reasons'])
            reasons_str = '• ' + reasons_str  # Add bullet to first item
            
            # Truncate long titles
            title = issue['title']
            if len(title) > 50:
                title = title[:47] + '...'
            
            # Format assignees
            assignees_str = ', '.join(issue['assignees']) if issue['assignees'] else 'Unassigned'
            
            print(f"| {repo_short} | [#{issue['number']}]({issue['url']}) | {title} | {assignees_str} | {reasons_str} |")
        
        # Summary statistics
        print(f"\n### Summary by Issue Type\n")
        reason_counts = defaultdict(int)
        for issue in flagged_issues:
            for reason in issue['reasons']:
                reason_counts[reason] += 1
        
        print("| Issue Type | Count |")
        print("|------------|-------|")
        for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"| {reason} | {count} |")
    else:
        print("🎉 No issues found with missing metadata!")


if __name__ == "__main__":
    main()

