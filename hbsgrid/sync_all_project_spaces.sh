#!/bin/bash

# Master script to sync all HBS grid project spaces to Dropbox simultaneously
# This script submits individual sync jobs using bsub for parallel execution

echo "Starting parallel sync of all HBS grid project spaces to Dropbox..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SINGLE_SYNC_SCRIPT="$SCRIPT_DIR/sync_single_project.sh"

# Check if the single project sync script exists
if [ ! -f "$SINGLE_SYNC_SCRIPT" ]; then
    echo "Error: sync_single_project.sh not found in $SCRIPT_DIR"
    exit 1
fi

# Make sure the single sync script is executable
chmod +x "$SINGLE_SYNC_SCRIPT"

# Array of all project names
PROJECTS=(
    "mmiller_commitee_votes"
    "mmiller_peps"
    "mmiller_colonialism"
    "mmiller_emrisk"
    "mmiller_bill_probability"
    "mmiller_foreign_influence"
    "mmiller_ownership_chains"
)

# Submit each project sync as a separate bsub job
JOB_IDS=()
for project in "${PROJECTS[@]}"; do
    echo "Submitting sync job for $project..."
    
    # Submit job and capture job ID
    JOB_OUTPUT=$(bsub -J "sync_${project}" -o "${project}_sync.log" -e "${project}_sync.err" "$SINGLE_SYNC_SCRIPT" "$project" 2>&1)
    
    if [ $? -eq 0 ]; then
        # Extract job ID from bsub output (format: "Job <12345> is submitted to queue <normal>.")
        JOB_ID=$(echo "$JOB_OUTPUT" | grep -o 'Job <[0-9]*>' | grep -o '[0-9]*')
        JOB_IDS+=("$JOB_ID")
        echo "  ✓ Job $JOB_ID submitted for $project"
    else
        echo "  ✗ Failed to submit job for $project"
        echo "    Error: $JOB_OUTPUT"
    fi
done

echo ""
echo "All sync jobs submitted!"
echo "Job IDs: ${JOB_IDS[*]}"
echo ""
echo "Monitor job status with:"
echo "  bjobs ${JOB_IDS[*]}"
echo ""
echo "View logs in current directory:"
for project in "${PROJECTS[@]}"; do
    echo "  ${project}: ${project}_sync.log (output), ${project}_sync.err (errors)"
done
echo ""
echo "Wait for all jobs to complete with:"
echo "  bwait ${JOB_IDS[*]}"
