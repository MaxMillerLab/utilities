#!/bin/bash

# Single project sync script for HBS grid to Dropbox
# Usage: ./sync_single_project.sh <project_name>

if [ $# -ne 1 ]; then
    echo "Usage: $0 <project_name>"
    echo "Available projects:"
    echo "  mmiller_commitee_votes"
    echo "  mmiller_peps"
    echo "  mmiller_colonialism"
    echo "  mmiller_emrisk"
    echo "  mmiller_bill_probability"
    echo "  mmiller_foreign_influence"
    echo "  mmiller_ownership_chains"
    exit 1
fi

PROJECT_NAME=$1

# Load rclone module
module load rclone

echo "Starting sync of $PROJECT_NAME to Dropbox..."

# Define project paths and sync accordingly
case $PROJECT_NAME in
    "mmiller_commitee_votes")
        SOURCE_PATH="/export/projects/mmiller_commitee_votes"
        ;;
    "mmiller_peps")
        SOURCE_PATH="/export/projects4/mmiller_peps"
        ;;
    "mmiller_colonialism")
        SOURCE_PATH="/export/projects4/mmiller_colonialism"
        ;;
    "mmiller_emrisk")
        SOURCE_PATH="/export/projects4/mmiller_emrisk"
        ;;
    "mmiller_bill_probability")
        SOURCE_PATH="/export/projects3/mmiller_bill_probability"
        ;;
    "mmiller_foreign_influence")
        SOURCE_PATH="/export/projects4/mmiller_foreign_influence"
        ;;
    "mmiller_ownership_chains")
        SOURCE_PATH="/export/projects4/mmiller_ownership_chains"
        ;;
    *)
        echo "Error: Unknown project name '$PROJECT_NAME'"
        echo "Available projects: mmiller_commitee_votes, mmiller_peps, mmiller_colonialism, mmiller_emrisk, mmiller_bill_probability, mmiller_foreign_influence, mmiller_ownership_chains"
        exit 1
        ;;
esac

echo "Syncing $PROJECT_NAME from $SOURCE_PATH..."
rclone sync "$SOURCE_PATH" "dropbox:hbsgrid/$PROJECT_NAME" --progress

if [ $? -eq 0 ]; then
    echo "Successfully synced $PROJECT_NAME to Dropbox!"
else
    echo "Error syncing $PROJECT_NAME to Dropbox!"
    exit 1
fi
