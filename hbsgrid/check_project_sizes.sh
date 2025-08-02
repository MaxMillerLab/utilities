#!/bin/bash

# Script to check the total size of all HBS grid project spaces
# Outputs individual project sizes and total in TB

echo "Checking sizes of all HBS grid project spaces..."
echo "================================================"

# Array of project names and their paths
declare -A PROJECTS
PROJECTS["mmiller_commitee_votes"]="/export/projects/mmiller_commitee_votes"
PROJECTS["mmiller_peps"]="/export/projects4/mmiller_peps"
PROJECTS["mmiller_colonialism"]="/export/projects4/mmiller_colonialism"
PROJECTS["mmiller_emrisk"]="/export/projects4/mmiller_emrisk"
PROJECTS["mmiller_bill_probability"]="/export/projects3/mmiller_bill_probability"
PROJECTS["mmiller_foreign_influence"]="/export/projects4/mmiller_foreign_influence"
PROJECTS["mmiller_ownership_chains"]="/export/projects4/mmiller_ownership_chains"

# Initialize total size in bytes
TOTAL_BYTES=0
ACCESSIBLE_PROJECTS=0
INACCESSIBLE_PROJECTS=0

# Function to convert bytes to human readable format
human_readable() {
    local bytes=$1
    if [ $bytes -lt 1024 ]; then
        echo "${bytes}B"
    elif [ $bytes -lt 1048576 ]; then
        echo "$(echo "scale=2; $bytes/1024" | bc)KB"
    elif [ $bytes -lt 1073741824 ]; then
        echo "$(echo "scale=2; $bytes/1048576" | bc)MB"
    elif [ $bytes -lt 1099511627776 ]; then
        echo "$(echo "scale=2; $bytes/1073741824" | bc)GB"
    else
        echo "$(echo "scale=2; $bytes/1099511627776" | bc)TB"
    fi
}

# Check each project
for project in "${!PROJECTS[@]}"; do
    path="${PROJECTS[$project]}"
    
    if [ -d "$path" ]; then
        echo -n "Checking $project... "
        
        # Get size in bytes using du
        size_output=$(du -sb "$path" 2>/dev/null)
        
        if [ $? -eq 0 ]; then
            # Extract size in bytes (first field)
            size_bytes=$(echo "$size_output" | cut -f1)
            TOTAL_BYTES=$((TOTAL_BYTES + size_bytes))
            ACCESSIBLE_PROJECTS=$((ACCESSIBLE_PROJECTS + 1))
            
            # Convert to human readable and TB
            size_human=$(human_readable $size_bytes)
            size_tb=$(echo "scale=4; $size_bytes/1099511627776" | bc)
            
            printf "%-40s %10s (%s TB)\n" "$size_human" "" "$size_tb"
        else
            echo "ERROR: Cannot read directory (permission denied)"
            INACCESSIBLE_PROJECTS=$((INACCESSIBLE_PROJECTS + 1))
        fi
    else
        echo "$project: Directory not found at $path"
        INACCESSIBLE_PROJECTS=$((INACCESSIBLE_PROJECTS + 1))
    fi
done

echo ""
echo "================================================"
echo "SUMMARY:"
echo "  Accessible projects: $ACCESSIBLE_PROJECTS"
echo "  Inaccessible projects: $INACCESSIBLE_PROJECTS"

if [ $ACCESSIBLE_PROJECTS -gt 0 ]; then
    # Calculate totals
    total_tb=$(echo "scale=4; $TOTAL_BYTES/1099511627776" | bc)
    total_gb=$(echo "scale=2; $TOTAL_BYTES/1073741824" | bc)
    total_human=$(human_readable $TOTAL_BYTES)
    
    echo ""
    echo "TOTAL SIZE:"
    echo "  Raw bytes: $TOTAL_BYTES"
    echo "  Human readable: $total_human"
    echo "  Gigabytes: ${total_gb} GB"
    echo "  Terabytes: ${total_tb} TB"
    
    if [ $INACCESSIBLE_PROJECTS -gt 0 ]; then
        echo ""
        echo "⚠️  Note: Total excludes $INACCESSIBLE_PROJECTS inaccessible project(s)"
    fi
else
    echo "❌ No accessible projects found!"
fi

echo ""
echo "Scan completed at $(date)"
