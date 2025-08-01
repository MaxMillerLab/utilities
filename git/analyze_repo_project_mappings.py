#!/usr/bin/env python3
"""
Analyze the existing data to discover repository-to-project mappings.
"""

import json
from pathlib import Path
from collections import defaultdict

def analyze_mappings():
    # Load data
    with open('data/issues.json', 'r') as f:
        issues_data = json.load(f)
    
    with open('data/projects.json', 'r') as f:
        projects_data = json.load(f)
    
    # Build a map of issue URLs to repositories
    url_to_repo = {}
    for repo_full, issues in issues_data['repositories'].items():
        repo_short = repo_full.split('/')[-1]
        for issue in issues:
            url_to_repo[issue['url']] = repo_short
    
    # Build a map of repositories to projects based on existing assignments
    repo_to_projects = defaultdict(lambda: defaultdict(int))
    
    # Check each project
    for project in projects_data['projects']:
        project_title = project['title']
        project_number = project['number']
        
        # Get items in this project
        project_items = projects_data.get('project_items', {}).get(str(project_number), {})
        items = project_items.get('items', [])
        
        # Count issues by repository
        for item in items:
            if item.get('content', {}).get('type') == 'Issue':
                issue_url = item.get('content', {}).get('url')
                if issue_url and issue_url in url_to_repo:
                    repo = url_to_repo[issue_url]
                    repo_to_projects[repo][project_title] += 1
    
    # Print the analysis
    print("Repository to Project Mapping Analysis")
    print("=" * 50)
    print()
    
    # Get all repositories
    all_repos = sorted(set(repo.split('/')[-1] for repo in issues_data['repositories'].keys()))
    
    for repo in all_repos:
        print(f"\n{repo}:")
        if repo in repo_to_projects:
            projects = repo_to_projects[repo]
            if projects:
                # Sort by count descending
                sorted_projects = sorted(projects.items(), key=lambda x: x[1], reverse=True)
                for project, count in sorted_projects:
                    print(f"  - {project}: {count} issues")
                # Suggest the most likely mapping
                most_likely = sorted_projects[0][0]
                print(f"  → Most likely project: {most_likely}")
            else:
                print("  - No issues in any project")
        else:
            print("  - No issues found in any project")
    
    # Generate the mapping dictionary
    print("\n\nSuggested REPO_TO_PROJECT_MAPPING:")
    print("{")
    for repo in all_repos:
        if repo in repo_to_projects and repo_to_projects[repo]:
            most_likely = sorted(repo_to_projects[repo].items(), key=lambda x: x[1], reverse=True)[0][0]
            print(f'    "{repo}": "{most_likely}",')
        else:
            print(f'    "{repo}": None,  # No existing mapping found')
    print("}")

if __name__ == "__main__":
    analyze_mappings()
