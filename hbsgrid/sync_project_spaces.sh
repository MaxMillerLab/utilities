#!/bin/bash

# Load rclone module
module load rclone

# Sync all HBS grid project spaces to Dropbox hbsgrid folder
echo "Starting sync of HBS grid project spaces to Dropbox..."

# Committee votes project
echo "Syncing mmiller_commitee_votes..."
rclone sync /export/projects/mmiller_commitee_votes "dropbox:hbsgrid/mmiller_commitee_votes" --progress

# PEPs project
echo "Syncing mmiller_peps..."
rclone sync /export/projects4/mmiller_peps "dropbox:hbsgrid/mmiller_peps" --progress

# Colonialism project
echo "Syncing mmiller_colonialism..."
rclone sync /export/projects4/mmiller_colonialism "dropbox:hbsgrid/mmiller_colonialism" --progress

# EM Risk project
echo "Syncing mmiller_emrisk..."
rclone sync /export/projects4/mmiller_emrisk "dropbox:hbsgrid/mmiller_emrisk" --progress

# Bill probability project
echo "Syncing mmiller_bill_probability..."
rclone sync /export/projects3/mmiller_bill_probability "dropbox:hbsgrid/mmiller_bill_probability" --progress

# Foreign influence project
echo "Syncing mmiller_foreign_influence..."
rclone sync /export/projects4/mmiller_foreign_influence "dropbox:hbsgrid/mmiller_foreign_influence" --progress

# Ownership chains project
echo "Syncing mmiller_ownership_chains..."
rclone sync /export/projects4/mmiller_ownership_chains "dropbox:hbsgrid/mmiller_ownership_chains" --progress

echo "All project spaces synced to Dropbox hbsgrid folder!"
