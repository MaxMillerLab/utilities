#!/bin/bash

# Script to find all directories starting with "mmiller_" in HBS grid project spaces
echo "Searching for mmiller_ projects across HBS grid..."
echo "=================================================="
echo

# Search in projects
echo "Searching in /export/projects/:"
if [ -d "/export/projects" ]; then
    find /export/projects -maxdepth 1 -type d -name "mmiller_*" 2>/dev/null | sort
    echo
else
    echo "  /export/projects not found or not accessible"
    echo
fi

# Search in projects1
echo "Searching in /export/projects1/:"
if [ -d "/export/projects1" ]; then
    find /export/projects1 -maxdepth 1 -type d -name "mmiller_*" 2>/dev/null | sort
    echo
else
    echo "  /export/projects1 not found or not accessible"
    echo
fi

# Search in projects2
echo "Searching in /export/projects2/:"
if [ -d "/export/projects2" ]; then
    find /export/projects2 -maxdepth 1 -type d -name "mmiller_*" 2>/dev/null | sort
    echo
else
    echo "  /export/projects2 not found or not accessible"
    echo
fi

# Search in projects3
echo "Searching in /export/projects3/:"
if [ -d "/export/projects3" ]; then
    find /export/projects3 -maxdepth 1 -type d -name "mmiller_*" 2>/dev/null | sort
    echo
else
    echo "  /export/projects3 not found or not accessible"
    echo
fi

# Search in projects4
echo "Searching in /export/projects4/:"
if [ -d "/export/projects4" ]; then
    find /export/projects4 -maxdepth 1 -type d -name "mmiller_*" 2>/dev/null | sort
    echo
else
    echo "  /export/projects4 not found or not accessible"
    echo
fi

# Summary count
echo "=================================================="
total_count=$(find /export/projects /export/projects1 /export/projects2 /export/projects3 /export/projects4 -maxdepth 1 -type d -name "mmiller_*" 2>/dev/null | wc -l)
echo "Total mmiller_ directories found: $total_count"
