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

# Sync everything — exclude only SQLite WAL/SHM files (transient) and noise.
# Qdrant is retired (ADR-005/ADR-006) — no exclude needed.
# data/embeddings/ (MLX-encoded dense retrieval shards, ~374M) is included:
# regenerating costs ~3h of MLX encoding via scripts/wiki/cold_encode.py.
rsync -av \
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
if [[ -d "$GDRIVE/embeddings" ]]; then
  find "$GDRIVE/embeddings" -type f -name 'shard-*.npy' | wc -l \
    | xargs echo "  Dense shards:"
  du -sh "$GDRIVE/embeddings" | awk '{print "  Embeddings size:", $1}'
fi
