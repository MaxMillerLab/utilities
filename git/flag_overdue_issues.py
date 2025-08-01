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
                    
                    # Handle multiple possible field names for target date across different projects
                    target_date = (
                        item.get('target completion date', '') or 
                        item.get('target end date', '') or
                        item.get('due date', '') or
                        item.get('deadline', '')
                    )
                    
                    issue_metadata[issue_url] = {
                        'project': project_title,
                        'project_number': project_number,
                        'status': item.get('status', ''),
                        'priority': item.get('priority', ''),
                        'start_date': item.get('start date', ''),
                        'target_date': target_date,
                        'fields': fields
                    }
    
    return issue_metadata


def parse_date(date_string):
    """Parse a date string and return a datetime object"""
    if not date_string:
        return None
    
    try:
        # Try ISO format first (YYYY-MM-DD)
        return datetime.strptime(date_string, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            # Try with time (YYYY-MM-DDTHH:MM:SSZ)
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except ValueError:
            print(f"Could not parse date: {date_string}", file=sys.stderr)
            return None


def is_overdue(target_date_str):
    """Check if a target date is in the past (end of day)"""
    target_date = parse_date(target_date_str)
    if not target_date:
        return False
    
    # Set target date to end of day (23:59:59)
    target_end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    now = datetime.now(timezone.utc)
    return target_end_of_day < now


def days_overdue(target_date_str):
    """Calculate how many days overdue an issue is"""
    target_date = parse_date(target_date_str)
    if not target_date:
        return 0
    
    # Set target date to end of day (23:59:59)
    target_end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    now = datetime.now(timezone.utc)
    if target_end_of_day >= now:
        return 0
    
    # Calculate days based on date difference, not exact time
    now_date = now.date()
    target_date_only = target_date.date()
    
    delta = now_date - target_date_only
    return delta.days


def analyze_overdue_issues(issues, issue_metadata):
    """Find all issues that are past their target completion date"""
    overdue_issues = []
    
    for issue in issues:
        url = issue['url']
        metadata = issue_metadata.get(url, {})
        target_date = metadata.get('target_date')
        
        if target_date and is_overdue(target_date):
            days = days_overdue(target_date)
            overdue_issues.append({
                'issue': issue,
                'metadata': metadata,
                'days_overdue': days,
                'target_date': target_date
            })
    
    return overdue_issues


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
    
    # Build metadata mapping for all issues across projects
    print("Building issue metadata from projects...", file=sys.stderr)
    issue_metadata = build_issue_project_metadata("MaxMillerLab", projects_data)
    print(f"Found metadata for {len(issue_metadata)} issues in projects\n", file=sys.stderr)
    
    all_overdue_issues = []
    total_issues = 0
    issues_with_target_dates = 0
    
    for repo in repos:
        print(f"Checking {repo}...", file=sys.stderr)
        issues = get_issues_for_repo(repo, issues_data)
        total_issues += len(issues)
        
        # Count issues with target dates
        for issue in issues:
            metadata = issue_metadata.get(issue['url'], {})
            if metadata.get('target_date'):
                issues_with_target_dates += 1
        
        overdue_issues = analyze_overdue_issues(issues, issue_metadata)
        
        for overdue_data in overdue_issues:
            all_overdue_issues.append({
                'repo': repo,
                'issue': overdue_data['issue'],
                'metadata': overdue_data['metadata'],
                'days_overdue': overdue_data['days_overdue'],
                'target_date': overdue_data['target_date'],
                'assignees': [assignee['login'] for assignee in overdue_data['issue'].get('assignees', [])]
            })
    
    # Sort by days overdue (most overdue first)
    all_overdue_issues.sort(key=lambda x: x['days_overdue'], reverse=True)
    
    # Export to CSV
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    csv_file = output_dir / "overdue_issues.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['repository', 'issue_number', 'title', 'assignees', 'target_date', 'days_overdue', 'status', 'priority', 'url'])
        writer.writeheader()
        
        for item in all_overdue_issues:
            issue = item['issue']
            metadata = item['metadata']
            writer.writerow({
                'repository': item['repo'].split('/')[-1],
                'issue_number': issue['number'],
                'title': issue['title'],
                'assignees': ','.join(item['assignees']) if item['assignees'] else '',
                'target_date': item['target_date'],
                'days_overdue': item['days_overdue'],
                'status': metadata.get('status', 'N/A'),
                'priority': metadata.get('priority', 'N/A'),
                'url': issue['url']
            })
    
    print(f"CSV data saved to: {csv_file}", file=sys.stderr)
    
    # Print markdown report
    print(f"\n## Overdue Issues Report\n")
    print(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")
    print(f"**Total open issues scanned:** {total_issues}")
    print(f"**Issues with target completion dates:** {issues_with_target_dates}")
    print(f"**Issues past their target date:** {len(all_overdue_issues)}\n")
    
    if all_overdue_issues:
        print("| Repository | Issue | Title | Assignees | Target Date | Days Overdue | Status | Priority |")
        print("|------------|-------|-------|-----------|-------------|--------------|--------|----------|")
        
        for item in all_overdue_issues:
            repo_short = item['repo'].split('/')[-1]
            issue = item['issue']
            metadata = item['metadata']
            
            # Truncate long titles
            title = issue['title']
            if len(title) > 40:
                title = title[:37] + '...'
            
            # Format status and priority
            status = metadata.get('status', 'N/A')
            priority = metadata.get('priority', 'N/A')
            
            # Format assignees
            assignees_str = ', '.join(item['assignees']) if item['assignees'] else 'Unassigned'
            
            print(f"| {repo_short} | [#{issue['number']}]({issue['url']}) | {title} | {assignees_str} | {item['target_date']} | {item['days_overdue']} | {status} | {priority} |")
        
        # Summary statistics
        print(f"\n### Summary Statistics\n")
        
        # Group by overdue periods
        periods = {
            '1-7 days': 0,
            '8-30 days': 0,
            '31-90 days': 0,
            '90+ days': 0
        }
        
        for item in all_overdue_issues:
            days = item['days_overdue']
            if days <= 7:
                periods['1-7 days'] += 1
            elif days <= 30:
                periods['8-30 days'] += 1
            elif days <= 90:
                periods['31-90 days'] += 1
            else:
                periods['90+ days'] += 1
        
        print("| Overdue Period | Count |")
        print("|----------------|-------|")
        for period, count in periods.items():
            if count > 0:
                print(f"| {period} | {count} |")
        
        # Group by repository
        print(f"\n### Overdue Issues by Repository\n")
        repo_counts = defaultdict(int)
        for item in all_overdue_issues:
            repo_short = item['repo'].split('/')[-1]
            repo_counts[repo_short] += 1
        
        print("| Repository | Overdue Count |")
        print("|------------|---------------|")
        for repo, count in sorted(repo_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"| {repo} | {count} |")
        
        # Group by priority
        print(f"\n### Overdue Issues by Priority\n")
        priority_counts = defaultdict(int)
        for item in all_overdue_issues:
            priority = item['metadata'].get('priority', 'No Priority')
            priority_counts[priority] += 1
        
        print("| Priority | Count |")
        print("|----------|-------|")
        for priority, count in sorted(priority_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"| {priority} | {count} |")
    else:
        print("🎉 No overdue issues found! All issues with target dates are on track.")


if __name__ == "__main__":
    main()
