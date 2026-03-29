#!/bin/bash
# Backup all data files to Google Drive
# Run: ./scripts/backup-data.sh

set -euo pipefail

GDRIVE="/Users/krisztiankoos/Library/CloudStorage/GoogleDrive-krisztian.koos@gmail.com/My Drive/Projects/learn-ukrainian-data"
SRC="/Users/krisztiankoos/projects/learn-ukrainian/data"

echo "=== Backing up data to Google Drive ==="
echo "Source: $SRC"
echo "Target: $GDRIVE"

mkdir -p "$GDRIVE"

# Sync everything — exclude only Qdrant storage (4.6G, regenerable from JSONL)
# and SQLite WAL/SHM files (transient)
rsync -av \
  --exclude='qdrant/' \
  --exclude='*.db-shm' \
  --exclude='*.db-wal' \
  --exclude='__pycache__/' \
  --exclude='.DS_Store' \
  "$SRC/" "$GDRIVE/"

# Show totals
echo ""
echo "=== Backup complete ==="
du -sh "$GDRIVE"
echo ""
echo "Files backed up:"
find "$GDRIVE" -type f | wc -l | xargs echo "  Total files:"
find "$GDRIVE" -name '*.jsonl' | wc -l | xargs echo "  JSONL files:"
find "$GDRIVE" -name '*.db' | wc -l | xargs echo "  SQLite DBs:"
