#!/bin/bash
# GitHub Police Report
# This script collects fresh GitHub data and runs all issue flagging scripts

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================================="
echo "GitHub Police Report - $(date)"
echo "=================================================="
echo ""

# Step 1: Collect fresh data
echo "Step 1: Collecting fresh GitHub data..."
echo "--------------------------------------------------"
python3 "$SCRIPT_DIR/collect_github_data.py"
if [ $? -ne 0 ]; then
    echo "Error: Failed to collect GitHub data"
    exit 1
fi
echo ""

# Step 2: Run stale issues report
echo "Step 2: Running stale issues report..."
echo "--------------------------------------------------"
mkdir -p "$SCRIPT_DIR/output"
python3 "$SCRIPT_DIR/flag_stale_issues.py" > "$SCRIPT_DIR/output/stale_issues_report.md"
if [ $? -ne 0 ]; then
    echo "Error: Failed to generate stale issues report"
else
    echo "Stale issues report saved to output/stale_issues_report.md"
    cat "$SCRIPT_DIR/output/stale_issues_report.md"
fi
echo ""

# Step 3: Run issues without info report
echo "Step 3: Running issues without info report..."
echo "--------------------------------------------------"
python3 "$SCRIPT_DIR/flag_issues_without_info.py" > "$SCRIPT_DIR/output/issues_without_info_report.md"
if [ $? -ne 0 ]; then
    echo "Error: Failed to generate issues without info report"
else
    echo "Issues without info report saved to output/issues_without_info_report.md"
    cat "$SCRIPT_DIR/output/issues_without_info_report.md"
fi
echo ""

# Step 4: Run overdue issues report
echo "Step 4: Running overdue issues report..."
echo "--------------------------------------------------"
python3 "$SCRIPT_DIR/flag_overdue_issues.py" > "$SCRIPT_DIR/output/overdue_issues_report.md"
if [ $? -ne 0 ]; then
    echo "Error: Failed to generate overdue issues report"
else
    echo "Overdue issues report saved to output/overdue_issues_report.md"
    cat "$SCRIPT_DIR/output/overdue_issues_report.md"
fi
echo ""

echo "=================================================="
echo "GitHub Police Report Complete!"
echo "=================================================="
echo ""
echo "Reports saved to:"
echo "  - output/stale_issues_report.md"
echo "  - output/issues_without_info_report.md"
echo "  - output/overdue_issues_report.md"
