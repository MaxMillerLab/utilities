#!/bin/bash

# Script to rename all files in current directory:
# 1. Convert to lowercase
# 2. Replace spaces with underscores

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Renaming files in current directory..."
echo "Converting to lowercase and replacing spaces with underscores"
echo

# Counter for renamed files
count=0

# Process all files in current directory (not subdirectories)
for file in *; do
    # Skip if it's a directory
    if [ -d "$file" ]; then
        continue
    fi
    
    # Convert to lowercase and replace spaces with underscores
    new_name=$(echo "$file" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
    
    # Only rename if the name would change
    if [ "$file" != "$new_name" ]; then
        # Check if target file already exists
        if [ -e "$new_name" ]; then
            echo -e "${RED}Warning: Cannot rename '$file' to '$new_name' - target file already exists${NC}"
        else
            mv "$file" "$new_name"
            echo -e "${GREEN}Renamed:${NC} '$file' ${YELLOW}→${NC} '$new_name'"
            ((count++))
        fi
    fi
done

echo
if [ $count -eq 0 ]; then
    echo "No files needed renaming."
else
    echo -e "${GREEN}Successfully renamed $count file(s).${NC}"
fi
